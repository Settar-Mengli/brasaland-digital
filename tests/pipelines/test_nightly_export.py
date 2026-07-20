"""Tests for scripts/nightly_export.py orchestration."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from collections.abc import Callable

from pipelines import job_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "nightly_export.py"


def _load_nightly_export() -> ModuleType:
    spec = importlib.util.spec_from_file_location("nightly_export_under_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["nightly_export_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def nightly(sqlite_db: None) -> ModuleType:
    return _load_nightly_export()


def test_target_date_unset_uses_previous_utc_day(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TARGET_DATE", raising=False)
    fixed = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    with patch.object(nightly, "datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        assert nightly.resolve_target_date() == date(2026, 7, 19)


def test_target_date_set_and_invalid(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-18")
    assert nightly.resolve_target_date() == date(2026, 7, 18)
    monkeypatch.setenv("TARGET_DATE", "bad")
    with pytest.raises(ValueError):
        nightly.resolve_target_date()


def test_week_start_monday_and_sunday_edges(nightly: ModuleType) -> None:
    assert nightly.week_start_for(date(2026, 7, 13)) == date(2026, 7, 13)  # Monday
    assert nightly.week_start_for(date(2026, 7, 19)) == date(2026, 7, 13)  # Sunday


def test_completed_skip_no_export_or_subprocess(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with patch.object(job_runner, "_utcnow", return_value=datetime.now(timezone.utc)):
        assert job_runner.claim_job("nightly_export", date(2026, 7, 19))[0]
        job_runner.mark_completed("nightly_export", date(2026, 7, 19))

    with (
        patch.object(nightly, "export_telemetry_csv") as export_mock,
        patch.object(nightly, "run_weekly_subprocess") as sub_mock,
        patch.object(nightly, "_export_with_fallback") as fallback_mock,
    ):
        code = nightly.main()
    assert code == 0
    export_mock.assert_not_called()
    fallback_mock.assert_not_called()
    sub_mock.assert_not_called()


def test_fresh_processing_skip_no_work(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with patch.object(job_runner, "_utcnow", return_value=datetime.now(timezone.utc)):
        assert job_runner.claim_job("nightly_export", date(2026, 7, 19))[0]

    with (
        patch.object(nightly, "_export_with_fallback") as fallback_mock,
        patch.object(nightly, "run_weekly_subprocess") as sub_mock,
    ):
        code = nightly.main()
    assert code == 0
    fallback_mock.assert_not_called()
    sub_mock.assert_not_called()


def test_existing_csv_skips_export_but_runs_pipeline(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    target = date(2026, 7, 19)
    csv_path = tmp_path / f"telemetry_{target.isoformat()}.csv"
    csv_path.write_text("id\n", encoding="utf-8")

    with (
        patch.object(nightly, "csv_path_for", return_value=csv_path),
        patch.object(nightly, "_export_with_fallback") as export_mock,
        patch.object(nightly, "run_weekly_subprocess") as sub_mock,
        patch.object(job_runner, "mark_completed") as mark_done,
    ):
        code = nightly.main()

    assert code == 0
    export_mock.assert_not_called()
    sub_mock.assert_called_once()
    mark_done.assert_called_once()


def test_export_half_open_bounds_and_header(
    nightly: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    seed_telemetry_row: Callable[..., None],
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    target = date(2026, 7, 19)
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    seed_telemetry_row(
        event_id="e1",
        event_type="ingredient_list_viewed",
        timestamp=start + timedelta(hours=1),
        tags={"location_id": "medellin_centro"},
        context={"sessionId": "s1"},
    )
    seed_telemetry_row(
        event_id="e-out",
        event_type="ingredient_list_viewed",
        timestamp=start + timedelta(days=1),
        tags={},
        context={},
    )
    destination = tmp_path / "telemetry_2026-07-19.csv"
    rows = nightly._export_with_fallback(target, destination)
    assert rows == 1
    text = destination.read_text(encoding="utf-8")
    assert text.splitlines()[0] == ",".join(nightly.CSV_COLUMNS)
    assert "e1" in text
    assert "e-out" not in text
    assert '"location_id": "medellin_centro"' in text or "location_id" in text


def test_subprocess_argv_and_uv_missing(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    fake_uv = r"C:\tools\uv.exe"
    completed = MagicMock(returncode=0, stderr="", stdout="")

    with (
        patch.object(nightly.shutil, "which", return_value=fake_uv),
        patch.object(nightly.subprocess, "run", return_value=completed) as run_mock,
        patch.object(nightly, "_export_with_fallback", return_value=0),
    ):
        assert nightly.main() == 0

    run_mock.assert_called_once()
    args, kwargs = run_mock.call_args
    argv = args[0]
    assert argv[0] == fake_uv
    assert argv[1:] == [
        "run",
        "--directory",
        "data",
        "--python",
        "3.13",
        "python",
        "-m",
        "pipelines.run_weekly",
        "--week-start",
        "2026-07-13",
    ]
    assert kwargs["shell"] is False
    assert kwargs["cwd"] == str(REPO_ROOT)
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert "DATABASE_URL" in kwargs["env"]


def test_uv_missing_marks_failed(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with (
        patch.object(nightly.shutil, "which", return_value=None),
        patch.object(nightly, "_export_with_fallback", return_value=0),
    ):
        code = nightly.main()
    assert code == 1
    row = job_runner.get_job_run("nightly_export", date(2026, 7, 19))
    assert row is not None
    assert row.status == "failed"
    assert row.error_message is not None
    assert "uv executable not found" in row.error_message


def test_nonzero_child_marks_failed(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    completed = MagicMock(returncode=2, stderr="pipeline blew up", stdout="")
    with (
        patch.object(nightly.shutil, "which", return_value="uv"),
        patch.object(nightly.subprocess, "run", return_value=completed),
        patch.object(nightly, "_export_with_fallback", return_value=0),
    ):
        code = nightly.main()
    assert code == 1
    row = job_runner.get_job_run("nightly_export", date(2026, 7, 19))
    assert row is not None
    assert row.status == "failed"
    assert "pipeline blew up" in (row.error_message or "")


def test_exception_leaves_failed_not_processing(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with patch.object(
        nightly, "_export_with_fallback", side_effect=RuntimeError("export boom")
    ):
        code = nightly.main()
    assert code == 1
    row = job_runner.get_job_run("nightly_export", date(2026, 7, 19))
    assert row is not None
    assert row.status == "failed"
    assert "export boom" in (row.error_message or "")


def test_terminal_write_failure_nonzero_recoverable(
    nightly: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TARGET_DATE", "2026-07-19")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("STALE_LOCK_HOURS", "6")
    completed = MagicMock(returncode=0, stderr="", stdout="")
    with (
        patch.object(nightly.shutil, "which", return_value="uv"),
        patch.object(nightly.subprocess, "run", return_value=completed),
        patch.object(nightly, "_export_with_fallback", return_value=0),
        patch.object(
            job_runner,
            "mark_completed",
            side_effect=RuntimeError("db down"),
        ),
        patch.object(job_runner, "mark_failed", side_effect=RuntimeError("db down")),
    ):
        code = nightly.main()
    assert code == 1
    # Row still processing — stale takeover can recover later.
    row = job_runner.get_job_run("nightly_export", date(2026, 7, 19))
    assert row is not None
    assert row.status == "processing"

    stale_now = datetime.now(timezone.utc) + timedelta(hours=7)
    with patch.object(job_runner, "_utcnow", return_value=stale_now):
        won, reason = job_runner.claim_job("nightly_export", date(2026, 7, 19))
    assert won is True
    assert reason == "claimed_stale_takeover"
