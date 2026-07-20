"""Celery tasks for reporting (async pipeline trigger + DLQ)."""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone

import database
from celery_app import celery_app
from pipelines.api import trigger_pipeline_run
from pipelines.db_models import TaskDeadLetter

logger = logging.getLogger(__name__)

# Exact prefix from data/pipelines/pipeline.py write_pipeline_run_start RuntimeError.
CONCURRENT_GUARD_PREFIX = "Concurrent run already Running"
MAX_ERROR_MESSAGE_CHARS = 2000
TASK_NAME = "reporting.run_pipeline_task"


def _is_concurrent_guard_error(exc: BaseException) -> bool:
    return isinstance(exc, RuntimeError) and str(exc).startswith(CONCURRENT_GUARD_PREFIX)


def _write_dead_letter(
    *,
    task_id: str,
    task_name: str,
    attempt_count: int,
    error_message: str,
) -> None:
    database.ensure_task_dead_letters_schema()
    bounded = error_message[:MAX_ERROR_MESSAGE_CHARS]
    now = datetime.now(timezone.utc)
    with database.get_session() as session:
        session.add(
            TaskDeadLetter(
                task_id=task_id,
                task_name=task_name,
                attempt_count=attempt_count,
                error_message=bounded,
                created_at=now,
            )
        )
        session.commit()


@celery_app.task(bind=True, max_retries=3, name=TASK_NAME)
def run_pipeline_task(self, week_start: str | None) -> dict:
    """Enqueue target: run weekly_location_performance_flow via pipelines.api."""
    task_id = self.request.id or "unknown"
    attempt = (self.request.retries or 0) + 1
    started = time.monotonic()
    parsed: date | None = None
    if week_start is not None:
        parsed = date.fromisoformat(week_start)

    logger.info(
        "task_id=%s attempt=%s status=started week_start=%s",
        task_id,
        attempt,
        week_start,
    )

    try:
        result = trigger_pipeline_run(week_start=parsed)
    except Exception as exc:
        duration = time.monotonic() - started
        if _is_concurrent_guard_error(exc):
            logger.error(
                "task_id=%s attempt=%s status=failure duration=%.3fs error=%s "
                "(non-retryable concurrent guard)",
                task_id,
                attempt,
                duration,
                exc,
            )
            raise

        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(
                "task_id=%s attempt=%s status=retry duration=%.3fs countdown=%s error=%s",
                task_id,
                attempt,
                duration,
                countdown,
                exc,
            )
            raise self.retry(exc=exc, countdown=countdown) from exc

        logger.error(
            "task_id=%s attempt=%s status=failure duration=%.3fs error=%s "
            "(retries exhausted; writing DLQ)",
            task_id,
            attempt,
            duration,
            exc,
        )
        _write_dead_letter(
            task_id=task_id,
            task_name=TASK_NAME,
            attempt_count=attempt,
            error_message=f"{type(exc).__name__}: {exc}",
        )
        raise

    duration = time.monotonic() - started
    logger.info(
        "task_id=%s attempt=%s status=success duration=%.3fs",
        task_id,
        attempt,
        duration,
    )
    return result
