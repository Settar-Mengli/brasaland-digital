from brasaland_shared.constants import VALID_STATUSES
from brasaland_shared.types import TransitionResult

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"in_progress", "discarded"}),
    "in_progress": frozenset({"resolved", "discarded"}),
    "resolved": frozenset(),
    "discarded": frozenset(),
}


def validate_transition(current: str, target: str) -> TransitionResult:
    if current not in VALID_STATUSES:
        return TransitionResult(
            is_allowed=False,
            message=f"unknown current status '{current}'",
        )

    if target not in VALID_STATUSES:
        return TransitionResult(
            is_allowed=False,
            message=f"unknown target status '{target}'",
        )

    if current == target:
        return TransitionResult(
            is_allowed=False,
            message=f"status is already '{current}'",
        )

    allowed_targets = _ALLOWED_TRANSITIONS[current]
    if not allowed_targets:
        return TransitionResult(
            is_allowed=False,
            message=f"cannot transition from a terminal state '{current}'",
        )

    if target in allowed_targets:
        return TransitionResult(is_allowed=True, message=None)

    if current == "open" and target == "resolved":
        return TransitionResult(
            is_allowed=False,
            message="open cannot move directly to resolved",
        )

    if current == "in_progress" and target == "open":
        return TransitionResult(
            is_allowed=False,
            message="in_progress cannot move back to open",
        )

    return TransitionResult(
        is_allowed=False,
        message=f"'{current}' cannot transition to '{target}'",
    )
