"""RFP ticket lifecycle transitions (sibling to incident lifecycle tests)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.lifecycle import validate_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("analyzing", "discarded"),
        ("analyzing", "intake_complete"),
        ("intake_complete", "drafting"),
        ("drafting", "under_evaluation"),
        ("under_evaluation", "waiting_for_approval"),
        ("waiting_for_approval", "done"),
    ],
)
def test_legal_transitions_are_allowed(current: str, target: str) -> None:
    result = validate_transition(current, target)

    assert result.is_allowed is True
    assert result.message is None


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("analyzing", "drafting"),
        ("analyzing", "done"),
        ("intake_complete", "analyzing"),
        ("intake_complete", "discarded"),
        ("drafting", "intake_complete"),
        ("under_evaluation", "drafting"),
        ("waiting_for_approval", "under_evaluation"),
        ("done", "waiting_for_approval"),
        ("discarded", "analyzing"),
        ("analyzing", "analyzing"),
        ("done", "done"),
    ],
)
def test_illegal_transitions_are_rejected(current: str, target: str) -> None:
    result = validate_transition(current, target)

    assert result.is_allowed is False
    assert result.message
    assert len(result.message) > 0


def test_discarded_terminal_rejects_all_outgoing() -> None:
    for target in (
        "analyzing",
        "intake_complete",
        "drafting",
        "under_evaluation",
        "waiting_for_approval",
        "done",
    ):
        result = validate_transition("discarded", target)
        assert result.is_allowed is False
        assert "terminal state 'discarded'" in result.message


def test_done_terminal_rejects_all_outgoing() -> None:
    for target in (
        "analyzing",
        "discarded",
        "intake_complete",
        "drafting",
        "under_evaluation",
        "waiting_for_approval",
    ):
        result = validate_transition("done", target)
        assert result.is_allowed is False
        assert "terminal state 'done'" in result.message


def test_unknown_current_status_is_rejected() -> None:
    result = validate_transition("frozen", "analyzing")

    assert result.is_allowed is False
    assert result.message == "unknown current status 'frozen'"


def test_unknown_target_status_is_rejected() -> None:
    result = validate_transition("analyzing", "frozen")

    assert result.is_allowed is False
    assert result.message == "unknown target status 'frozen'"
