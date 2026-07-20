"""Unit tests for pipelines.job_runner atomic claim and transitions."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from pipelines import job_runner
from pipelines.db_models import JobRun

TARGET = date(2026, 7, 19)
JOB = "nightly_export"


def _now() -> datetime:
    return datetime(2026, 7, 20, 0, 15, tzinfo=timezone.utc)


def test_first_claim_wins(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is True
    assert reason == "claimed"
    row = job_runner.get_job_run(JOB, TARGET)
    assert row is not None
    assert row.status == "processing"
    assert row.started_at.replace(tzinfo=timezone.utc) == _now()


def test_second_claim_loses_to_fresh_processing(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is False
    assert reason == "skipped_running"


def test_completed_skip(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
        job_runner.mark_completed(JOB, TARGET)
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is False
    assert reason == "skipped_completed"
    assert job_runner.has_completed_for_date(JOB, TARGET) is True


def test_failed_retry_transition(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
        job_runner.mark_failed(JOB, TARGET, "boom")
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is True
    assert reason == "claimed_retry"
    row = job_runner.get_job_run(JOB, TARGET)
    assert row is not None
    assert row.status == "processing"
    assert row.error_message is None
    assert row.finished_at is None


def test_stale_processing_takeover(sqlite_db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STALE_LOCK_HOURS", "6")
    stale_started = _now() - timedelta(hours=7)
    with patch.object(job_runner, "_utcnow", return_value=stale_started):
        assert job_runner.claim_job(JOB, TARGET)[0] is True

    with patch.object(job_runner, "_utcnow", return_value=_now()):
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is True
    assert reason == "claimed_stale_takeover"
    row = job_runner.get_job_run(JOB, TARGET)
    assert row is not None
    assert row.status == "processing"
    assert row.started_at.replace(tzinfo=timezone.utc) == _now()


def test_fresh_processing_not_stale(sqlite_db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STALE_LOCK_HOURS", "6")
    with patch.object(job_runner, "_utcnow", return_value=_now() - timedelta(hours=1)):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is False
    assert reason == "skipped_running"


def test_rowcount_race_loss_on_failed_retry(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
        job_runner.mark_failed(JOB, TARGET, "boom")

    with (
        patch.object(job_runner, "_utcnow", return_value=_now()),
        patch.object(
            job_runner,
            "_transition_failed_to_processing",
            return_value=False,
        ),
    ):
        won, reason = job_runner.claim_job(JOB, TARGET)
    assert won is False
    assert reason == "skipped_running"


def test_predicates(sqlite_db: None) -> None:
    assert job_runner.has_processing_lock(JOB, TARGET) is False
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        job_runner.claim_job(JOB, TARGET)
    assert job_runner.has_processing_lock(JOB, TARGET) is True
    assert job_runner.has_completed_for_date(JOB, TARGET) is False


def test_mark_completed_and_failed_bound_error(sqlite_db: None) -> None:
    with patch.object(job_runner, "_utcnow", return_value=_now()):
        job_runner.claim_job(JOB, TARGET)
        long_message = "x" * 5000
        job_runner.mark_failed(JOB, TARGET, long_message)
    row = job_runner.get_job_run(JOB, TARGET)
    assert row is not None
    assert row.status == "failed"
    assert row.error_message is not None
    assert len(row.error_message) <= job_runner.MAX_ERROR_MESSAGE_CHARS

    with patch.object(job_runner, "_utcnow", return_value=_now()):
        assert job_runner.claim_job(JOB, TARGET)[0] is True
        job_runner.mark_completed(JOB, TARGET)
    row = job_runner.get_job_run(JOB, TARGET)
    assert row is not None
    assert row.status == "completed"
    assert row.error_message is None


def test_ensure_schema_creates_only_job_runs(sqlite_db: None) -> None:
    job_runner._schema_ready = False
    job_runner.ensure_schema()
    assert job_runner._engine is not None
    with Session(job_runner._engine) as session:
        rows = session.exec(select(JobRun)).all()
    assert rows == []


def test_stale_lock_hours_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STALE_LOCK_HOURS", raising=False)
    assert job_runner.stale_lock_hours() == 6.0
    monkeypatch.setenv("STALE_LOCK_HOURS", "0")
    with pytest.raises(ValueError):
        job_runner.stale_lock_hours()
    monkeypatch.setenv("STALE_LOCK_HOURS", "nope")
    with pytest.raises(ValueError):
        job_runner.stale_lock_hours()
