"""Nightly telemetry export + weekly pipeline trigger (DEV-53).

Environment:
  TARGET_DATE=YYYY-MM-DD
      Optional UTC calendar day to export. When unset, uses the previous UTC day
      (datetime.now(timezone.utc).date() - timedelta(days=1)).
  STALE_LOCK_HOURS
      Hours before a processing job_runs row is treated as orphaned (default 6).
  DATABASE_URL
      Required Postgres URL (also loaded from data/.env then services/inventory/.env).

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/nightly_export.py

Direct execution also works after sys.path bootstrap::

    python scripts/nightly_export.py
"""

from __future__ import annotations

import csv
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

from pipelines import job_runner  # noqa: E402

JOB_NAME = "nightly_export"
CSV_COLUMNS = (
    "id",
    "event_id",
    "event_type",
    "timestamp",
    "service",
    "level",
    "tags",
    "context",
)
MAX_STDERR_CHARS = 2000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("nightly_export")


def resolve_target_date() -> date:
    """Resolve TARGET_DATE env (YYYY-MM-DD) or previous UTC day."""
    raw = os.environ.get("TARGET_DATE")
    if raw is None or raw.strip() == "":
        return datetime.now(timezone.utc).date() - timedelta(days=1)
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise ValueError(
            f"TARGET_DATE must be YYYY-MM-DD, got {raw!r}"
        ) from exc


def week_start_for(target: date) -> date:
    """Monday (ISO) of the ISO week containing target."""
    return target - timedelta(days=target.weekday())


def resolve_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    load_dotenv(DATA_ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    load_dotenv(REPO_ROOT / "services" / "inventory" / ".env")
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    raise RuntimeError(
        "DATABASE_URL is not set. Export it or add it to data/.env or "
        "services/inventory/.env"
    )


def _serialize_json_field(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        return json.dumps(parsed, sort_keys=True, default=str)
    return json.dumps(value, sort_keys=True, default=str)


def _format_timestamp(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def csv_path_for(target: date) -> Path:
    return DATA_ROOT / "raw" / f"telemetry_{target.isoformat()}.csv"


def export_telemetry_csv(target: date, destination: Path) -> int:
    """Stream telemetry_events for the UTC day into destination. Returns row count."""
    start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".tmp")

    sql = text(
        """
        SELECT id, event_id, event_type, timestamp, service, level, tags, context
        FROM public.telemetry_events
        WHERE timestamp >= :start AND timestamp < :end
        ORDER BY timestamp ASC, id ASC
        """
    )

    engine = job_runner.get_engine()
    written = 0
    try:
        with engine.connect() as conn:
            result = conn.execution_options(stream_results=True, yield_per=500).execute(
                sql,
                {"start": start, "end": end},
            )
            with temp_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(CSV_COLUMNS))
                writer.writeheader()
                for row in result:
                    mapping = row._mapping
                    writer.writerow(
                        {
                            "id": mapping["id"],
                            "event_id": mapping["event_id"],
                            "event_type": mapping["event_type"],
                            "timestamp": _format_timestamp(mapping["timestamp"]),
                            "service": mapping["service"],
                            "level": mapping["level"],
                            "tags": _serialize_json_field(mapping["tags"]),
                            "context": _serialize_json_field(mapping["context"]),
                        }
                    )
                    written += 1
        os.replace(temp_path, destination)
    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise
    return written


def run_weekly_subprocess(week_start: date, child_env: dict[str, str]) -> None:
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise RuntimeError("uv executable not found on PATH")

    argv = [
        uv_path,
        "run",
        "--directory",
        "data",
        "--python",
        "3.13",
        "python",
        "-m",
        "pipelines.run_weekly",
        "--week-start",
        week_start.isoformat(),
    ]
    completed = subprocess.run(
        argv,
        shell=False,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=child_env,
        check=False,
    )
    if completed.returncode != 0:
        stderr_tail = (completed.stderr or completed.stdout or "")[-MAX_STDERR_CHARS:]
        raise RuntimeError(
            f"pipeline subprocess exited non-zero ({completed.returncode}): "
            f"{stderr_tail}"
        )


def _log(level: int, *, target_date: date, status: str, message: str) -> None:
    logger.log(
        level,
        "job_name=%s target_date=%s status=%s %s",
        JOB_NAME,
        target_date.isoformat(),
        status,
        message,
    )


def main() -> int:
    target = resolve_target_date()
    monday = week_start_for(target)
    os.environ["DATABASE_URL"] = resolve_database_url()
    child_env = os.environ.copy()

    won, reason = job_runner.claim_job(JOB_NAME, target)
    if not won:
        if reason == "skipped_completed":
            _log(
                logging.INFO,
                target_date=target,
                status="completed",
                message="skipped: duplicate",
            )
            return 0
        _log(
            logging.INFO,
            target_date=target,
            status="processing",
            message="skipped: already running",
        )
        return 0

    _log(
        logging.INFO,
        target_date=target,
        status="processing",
        message="started",
    )

    try:
        destination = csv_path_for(target)
        if destination.exists():
            _log(
                logging.INFO,
                target_date=target,
                status="processing",
                message=f"csv exists, skip export path={destination}",
            )
        else:
            # SQLite tests use unqualified telemetry_events; production uses public.
            rows = _export_with_fallback(target, destination)
            _log(
                logging.INFO,
                target_date=target,
                status="processing",
                message=f"csv exported rows={rows} path={destination}",
            )

        run_weekly_subprocess(monday, child_env)
        job_runner.mark_completed(JOB_NAME, target)
        _log(
            logging.INFO,
            target_date=target,
            status="completed",
            message=f"completed csv={destination} week_start={monday.isoformat()}",
        )
        return 0
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        logger.exception(
            "job_name=%s target_date=%s status=failed %s",
            JOB_NAME,
            target.isoformat(),
            error_text,
        )
        try:
            job_runner.mark_failed(JOB_NAME, target, error_text)
        except Exception:
            logger.exception(
                "job_name=%s target_date=%s status=failed terminal finalize failed",
                JOB_NAME,
                target.isoformat(),
            )
        return 1


def _export_with_fallback(target: date, destination: Path) -> int:
    """Export using public.telemetry_events; fall back for SQLite tests."""
    try:
        return export_telemetry_csv(target, destination)
    except Exception as first_error:
        # SQLite in-memory fixtures have no public schema — retry unqualified.
        dialect = job_runner.get_engine().dialect.name
        if dialect != "sqlite":
            raise first_error
        start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_suffix(destination.suffix + ".tmp")
        sql = text(
            """
            SELECT id, event_id, event_type, timestamp, service, level, tags, context
            FROM telemetry_events
            WHERE timestamp >= :start AND timestamp < :end
            ORDER BY timestamp ASC, id ASC
            """
        )
        written = 0
        try:
            with job_runner.get_engine().connect() as conn:
                result = conn.execution_options(
                    stream_results=True, yield_per=500
                ).execute(sql, {"start": start, "end": end})
                with temp_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(CSV_COLUMNS))
                    writer.writeheader()
                    for row in result:
                        mapping = row._mapping
                        writer.writerow(
                            {
                                "id": mapping["id"],
                                "event_id": mapping["event_id"],
                                "event_type": mapping["event_type"],
                                "timestamp": _format_timestamp(mapping["timestamp"]),
                                "service": mapping["service"],
                                "level": mapping["level"],
                                "tags": _serialize_json_field(mapping["tags"]),
                                "context": _serialize_json_field(mapping["context"]),
                            }
                        )
                        written += 1
            os.replace(temp_path, destination)
        except Exception:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise
        return written


if __name__ == "__main__":
    raise SystemExit(main())
