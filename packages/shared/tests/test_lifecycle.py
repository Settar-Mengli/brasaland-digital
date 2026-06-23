import pytest

from brasaland_shared.lifecycle import validate_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("open", "in_progress"),
        ("open", "discarded"),
        ("in_progress", "resolved"),
        ("in_progress", "discarded"),
    ],
)
def test_legal_transitions_are_allowed(current: str, target: str) -> None:
    result = validate_transition(current, target)

    assert result.is_allowed is True
    assert result.message is None


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("resolved", "open"),
        ("resolved", "in_progress"),
        ("resolved", "discarded"),
        ("discarded", "open"),
        ("discarded", "in_progress"),
        ("discarded", "resolved"),
        ("open", "resolved"),
        ("in_progress", "open"),
        ("resolved", "resolved"),
        ("discarded", "discarded"),
    ],
)
def test_illegal_transitions_are_rejected(current: str, target: str) -> None:
    result = validate_transition(current, target)

    assert result.is_allowed is False
    assert result.message
    assert len(result.message) > 0


def test_resolved_terminal_rejects_all_outgoing() -> None:
    for target in ("open", "in_progress", "discarded"):
        result = validate_transition("resolved", target)
        assert result.is_allowed is False
        assert "terminal state 'resolved'" in result.message


def test_discarded_terminal_rejects_all_outgoing() -> None:
    for target in ("open", "in_progress", "resolved"):
        result = validate_transition("discarded", target)
        assert result.is_allowed is False
        assert "terminal state 'discarded'" in result.message


def test_open_cannot_move_directly_to_resolved() -> None:
    result = validate_transition("open", "resolved")

    assert result.is_allowed is False
    assert result.message == "open cannot move directly to resolved"


def test_in_progress_cannot_move_back_to_open() -> None:
    result = validate_transition("in_progress", "open")

    assert result.is_allowed is False
    assert result.message == "in_progress cannot move back to open"


def test_unknown_current_status_is_rejected() -> None:
    result = validate_transition("frozen", "open")

    assert result.is_allowed is False
    assert result.message == "unknown current status 'frozen'"


def test_unknown_target_status_is_rejected() -> None:
    result = validate_transition("open", "frozen")

    assert result.is_allowed is False
    assert result.message == "unknown target status 'frozen'"
