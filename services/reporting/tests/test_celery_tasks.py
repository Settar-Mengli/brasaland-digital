"""Unit tests for run_pipeline_task (eager Celery; no live Redis)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from sqlmodel import Session, select

import database
from pipelines.db_models import TaskDeadLetter
from tasks import CONCURRENT_GUARD_PREFIX, run_pipeline_task


@pytest.fixture
def eager_celery(monkeypatch: pytest.MonkeyPatch) -> None:
    from celery_app import celery_app

    monkeypatch.setitem(celery_app.conf, "task_always_eager", True)
    monkeypatch.setitem(celery_app.conf, "task_eager_propagates", True)


def test_guard_error_does_not_retry(eager_celery: None, sqlite_db: None) -> None:
    # Real prefix from data/pipelines/pipeline.py:246-248
    guard_exc = RuntimeError(
        f"{CONCURRENT_GUARD_PREFIX} for week_start=2026-07-07 "
        f"(run_id=11111111-1111-1111-1111-111111111111)"
    )
    assert str(guard_exc).startswith(CONCURRENT_GUARD_PREFIX)

    run_pipeline_task.push_request(id="task-guard-1", retries=0)
    try:
        with (
            patch("tasks.trigger_pipeline_run", side_effect=guard_exc),
            patch.object(run_pipeline_task, "retry") as mock_retry,
        ):
            with pytest.raises(RuntimeError, match=CONCURRENT_GUARD_PREFIX):
                run_pipeline_task(None)
        mock_retry.assert_not_called()
    finally:
        run_pipeline_task.pop_request()

    with Session(database.get_engine()) as session:
        assert session.exec(select(TaskDeadLetter)).all() == []


def test_retryable_error_retries_with_backoff(
    eager_celery: None, sqlite_db: None
) -> None:
    retryable = RuntimeError("transient db blip")
    run_pipeline_task.push_request(id="task-retry-1", retries=0)
    try:
        with (
            patch("tasks.trigger_pipeline_run", side_effect=retryable),
            patch.object(
                run_pipeline_task,
                "retry",
                side_effect=lambda **kw: (_ for _ in ()).throw(Retry(when=kw["countdown"])),
            ) as mock_retry,
        ):
            with pytest.raises(Retry) as raised:
                run_pipeline_task(None)
        mock_retry.assert_called_once()
        assert mock_retry.call_args.kwargs["countdown"] == 2**0
        assert raised.value.when == 2**0
    finally:
        run_pipeline_task.pop_request()


def test_retry_countdown_formula_on_second_attempt(
    eager_celery: None, sqlite_db: None
) -> None:
    retryable = RuntimeError("again")
    run_pipeline_task.push_request(id="task-retry-2", retries=2)
    try:
        with (
            patch("tasks.trigger_pipeline_run", side_effect=retryable),
            patch.object(
                run_pipeline_task,
                "retry",
                side_effect=lambda **kw: (_ for _ in ()).throw(Retry(when=kw["countdown"])),
            ) as mock_retry,
        ):
            with pytest.raises(Retry) as raised:
                run_pipeline_task(None)
        mock_retry.assert_called_once()
        assert mock_retry.call_args.kwargs["countdown"] == 2**2
        assert raised.value.when == 2**2
    finally:
        run_pipeline_task.pop_request()


def test_exhaustion_writes_dlq(eager_celery: None, sqlite_db: None) -> None:
    final_exc = RuntimeError("permanent failure")
    run_pipeline_task.push_request(id="task-dlq-1", retries=3)
    try:
        with (
            patch("tasks.trigger_pipeline_run", side_effect=final_exc),
            patch.object(run_pipeline_task, "retry") as mock_retry,
        ):
            with pytest.raises(RuntimeError, match="permanent failure"):
                run_pipeline_task(None)
        mock_retry.assert_not_called()
    finally:
        run_pipeline_task.pop_request()

    with Session(database.get_engine()) as session:
        rows = session.exec(select(TaskDeadLetter)).all()
    assert len(rows) == 1
    assert rows[0].task_id == "task-dlq-1"
    assert rows[0].task_name == "reporting.run_pipeline_task"
    assert rows[0].attempt_count == 4
    assert rows[0].error_message is not None
    assert "permanent failure" in rows[0].error_message
