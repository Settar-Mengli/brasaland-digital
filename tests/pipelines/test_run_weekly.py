"""CLI tests for pipelines.run_weekly."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from pipelines import run_weekly


def test_valid_monday_calls_flow_with_date() -> None:
    monday = date(2026, 7, 13)
    with patch.object(
        run_weekly,
        "weekly_location_performance_flow",
        create=True,
    ):
        # Import path used inside main — patch the pipeline symbol after import hook.
        with patch(
            "pipelines.pipeline.weekly_location_performance_flow",
            return_value={"ok": True},
        ) as mock_flow:
            code = run_weekly.main(["--week-start", monday.isoformat()])
    assert code == 0
    mock_flow.assert_called_once_with(week_start=monday)


def test_non_monday_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_weekly.main(["--week-start", "2026-07-14"])
    assert exc_info.value.code != 0


def test_malformed_date_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_weekly.main(["--week-start", "not-a-date"])
    assert exc_info.value.code != 0


def test_flow_exception_propagates() -> None:
    with patch(
        "pipelines.pipeline.weekly_location_performance_flow",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            run_weekly.main(["--week-start", "2026-07-13"])
