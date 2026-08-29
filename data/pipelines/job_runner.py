"""Atomic nightly job state control for reporting.job_runs."""

from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from pipelines.db_models import JobRun

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

DEFAULT_STALE_LOCK_HOURS = 6
MAX_ERROR_MESSAGE_CHARS = 2000
TERMINAL_RETRY_ATTEMPTS = 3
TERMINAL_RETRY_DELAY_SECONDS = 0.5

_engine: Engine | None = None
_schema_ready = False


def get_engine() -> Engine:
    """Lazy engine so importing this module never opens a database connection."""
    global _engine
    if _engine is not None:
        return _engine

    url = os.environ.get("REPORTING_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        load_dotenv()
        url = os.environ.get("REPORTING_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")

    _engine = create_engine(url, echo=False, pool_pre_ping=True)
    return _engine


def ensure_schema() -> None:
    """Create reporting.job_runs on SQLite test hosts only."""
    global _schema_ready
    if _schema_ready:
        return

    engine = get_engine()
    if engine.dialect.name == "postgresql":
        _schema_ready = True
        return

    import pipelines.db_models  # noqa: F401 — register JobRun on metadata

    SQLModel.metadata.create_all(engine, tables=[JobRun.__table__])
    _schema_ready = True


def stale_lock_hours() -> float:
    """Return positive STALE_LOCK_HOURS from env (default 6)."""
    raw = os.environ.get("STALE_LOCK_HOURS")
    if raw is None or raw.strip() == "":
        return float(DEFAULT_STALE_LOCK_HOURS)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"STALE_LOCK_HOURS must be a positive number, got {raw!r}"
        ) from exc
    if value <= 0:
        raise ValueError(f"STALE_LOCK_HOURS must be positive, got {value}")
    return value


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _bound_error(message: str | None) -> str | None:
    if message is None:
        return None
    if len(message) <= MAX_ERROR_MESSAGE_CHARS:
        return message
    return message[: MAX_ERROR_MESSAGE_CHARS - 3] + "..."


def _get_job_run(session: Session, job_name: str, target_date: date) -> JobRun | None:
    return session.exec(
        select(JobRun).where(
            JobRun.job_name == job_name,
            JobRun.target_date == target_date,
        )
    ).first()


def get_job_run(job_name: str, target_date: date) -> JobRun | None:
    """Return the job_runs row for (job_name, target_date), if any."""
    ensure_schema()
    with Session(get_engine()) as session:
        return _get_job_run(session, job_name, target_date)


def has_processing_lock(job_name: str, target_date: date) -> bool:
    """True when a processing row exists for the job/date."""
    row = get_job_run(job_name, target_date)
    return row is not None and row.status == STATUS_PROCESSING


def has_completed_for_date(job_name: str, target_date: date) -> bool:
    """True when a completed row exists for the job/date."""
    row = get_job_run(job_name, target_date)
    return row is not None and row.status == STATUS_COMPLETED


def _is_fresh_processing(row: JobRun, now: datetime) -> bool:
    started = row.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    cutoff = now - timedelta(hours=stale_lock_hours())
    return started >= cutoff


def _claim_insert(session: Session, job_name: str, target_date: date, now: datetime) -> bool:
    values: dict[str, Any] = {
        "job_name": job_name,
        "target_date": target_date,
        "status": STATUS_PROCESSING,
        "started_at": now,
        "finished_at": None,
        "error_message": None,
        "created_at": now,
    }
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        statement = pg_insert(JobRun).values(**values)
    else:
        statement = sqlite_insert(JobRun).values(**values)
    statement = statement.on_conflict_do_nothing(
        index_elements=["job_name", "target_date"]
    )
    result = session.execute(statement)
    session.commit()
    return (result.rowcount or 0) > 0


def _transition_failed_to_processing(
    session: Session, job_name: str, target_date: date, now: datetime
) -> bool:
    statement = (
        update(JobRun)
        .where(JobRun.job_name == job_name)
        .where(JobRun.target_date == target_date)
        .where(JobRun.status == STATUS_FAILED)
        .values(
            status=STATUS_PROCESSING,
            started_at=now,
            finished_at=None,
            error_message=None,
        )
    )
    result = session.execute(statement)
    session.commit()
    return (result.rowcount or 0) > 0


def _mark_stale_failed(
    session: Session, job_name: str, target_date: date, now: datetime
) -> bool:
    statement = (
        update(JobRun)
        .where(JobRun.job_name == job_name)
        .where(JobRun.target_date == target_date)
        .where(JobRun.status == STATUS_PROCESSING)
        .values(
            status=STATUS_FAILED,
            finished_at=now,
            error_message="stale lock takeover",
        )
    )
    result = session.execute(statement)
    session.commit()
    return (result.rowcount or 0) > 0


def claim_job(job_name: str, target_date: date) -> tuple[bool, str]:
    """Atomically claim a nightly job run.

    Returns ``(won, reason)`` where reason is one of:
    ``claimed``, ``skipped_completed``, ``skipped_running``, ``claimed_retry``,
    ``claimed_stale_takeover``.
    """
    ensure_schema()
    now = _utcnow()
    with Session(get_engine()) as session:
        if _claim_insert(session, job_name, target_date, now):
            return True, "claimed"

        existing = _get_job_run(session, job_name, target_date)
        if existing is None:
            # Concurrent delete / unexpected race — try insert once more.
            if _claim_insert(session, job_name, target_date, now):
                return True, "claimed"
            return False, "skipped_running"

        if existing.status == STATUS_COMPLETED:
            return False, "skipped_completed"

        if existing.status == STATUS_PROCESSING:
            if _is_fresh_processing(existing, now):
                return False, "skipped_running"
            if not _mark_stale_failed(session, job_name, target_date, now):
                return False, "skipped_running"
            if _transition_failed_to_processing(session, job_name, target_date, now):
                return True, "claimed_stale_takeover"
            return False, "skipped_running"

        if existing.status == STATUS_FAILED:
            if _transition_failed_to_processing(session, job_name, target_date, now):
                return True, "claimed_retry"
            return False, "skipped_running"

        # Unexpected status (e.g. pending) — treat as not claimable without overwrite.
        return False, "skipped_running"


def _finalize_with_retry(
    job_name: str,
    target_date: date,
    *,
    status: str,
    error_message: str | None,
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, TERMINAL_RETRY_ATTEMPTS + 1):
        try:
            ensure_schema()
            now = _utcnow()
            with Session(get_engine()) as session:
                statement = (
                    update(JobRun)
                    .where(JobRun.job_name == job_name)
                    .where(JobRun.target_date == target_date)
                    .where(JobRun.status == STATUS_PROCESSING)
                    .values(
                        status=status,
                        finished_at=now,
                        error_message=_bound_error(error_message),
                    )
                )
                result = session.execute(statement)
                session.commit()
                if (result.rowcount or 0) > 0:
                    return
                # Row may already be terminal; treat as success if matching status.
                row = _get_job_run(session, job_name, target_date)
                if row is not None and row.status == status:
                    return
                raise RuntimeError(
                    f"failed to finalize job_runs to {status} for "
                    f"{job_name}/{target_date} (rowcount=0)"
                )
        except Exception as exc:  # noqa: BLE001 — retry then propagate
            last_error = exc
            logger.warning(
                "terminal finalize attempt %s/%s failed: %s",
                attempt,
                TERMINAL_RETRY_ATTEMPTS,
                exc,
            )
            if attempt < TERMINAL_RETRY_ATTEMPTS:
                time.sleep(TERMINAL_RETRY_DELAY_SECONDS)
    assert last_error is not None
    raise last_error


def mark_completed(job_name: str, target_date: date) -> None:
    """Mark a processing job as completed (best-effort with retries)."""
    _finalize_with_retry(
        job_name, target_date, status=STATUS_COMPLETED, error_message=None
    )


def mark_failed(job_name: str, target_date: date, error_message: str) -> None:
    """Mark a processing job as failed (best-effort with retries)."""
    _finalize_with_retry(
        job_name,
        target_date,
        status=STATUS_FAILED,
        error_message=error_message,
    )
