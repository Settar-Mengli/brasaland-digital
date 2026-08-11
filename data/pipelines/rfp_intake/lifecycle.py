"""RFP ticket status machine (sibling to brasaland_shared incident lifecycle)."""

from __future__ import annotations

from dataclasses import dataclass

RFP_STATUSES: frozenset[str] = frozenset(
    {
        "analyzing",
        "discarded",
        "intake_complete",
        "drafting",
        "under_evaluation",
        "waiting_for_approval",
        "done",
    }
)

# Part 1 chain only. P2 will extend under_evaluation (back-edge to drafting +
# needs_human_review). P3 will extend waiting_for_approval (reject /
# request_changes). Those edges are additive and authored per-part.
RFP_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "analyzing": frozenset({"discarded", "intake_complete"}),
    "discarded": frozenset(),  # terminal
    "intake_complete": frozenset({"drafting"}),
    "drafting": frozenset({"under_evaluation"}),
    "under_evaluation": frozenset({"waiting_for_approval"}),
    "waiting_for_approval": frozenset({"done"}),
    "done": frozenset(),  # terminal
}


@dataclass(frozen=True)
class TransitionResult:
    is_allowed: bool
    message: str | None


def validate_transition(current: str, target: str) -> TransitionResult:
    if current not in RFP_STATUSES:
        return TransitionResult(
            is_allowed=False,
            message=f"unknown current status '{current}'",
        )

    if target not in RFP_STATUSES:
        return TransitionResult(
            is_allowed=False,
            message=f"unknown target status '{target}'",
        )

    if current == target:
        return TransitionResult(
            is_allowed=False,
            message=f"status is already '{current}'",
        )

    allowed_targets = RFP_ALLOWED_TRANSITIONS[current]
    if not allowed_targets:
        return TransitionResult(
            is_allowed=False,
            message=f"cannot transition from a terminal state '{current}'",
        )

    if target in allowed_targets:
        return TransitionResult(is_allowed=True, message=None)

    return TransitionResult(
        is_allowed=False,
        message=f"'{current}' cannot transition to '{target}'",
    )
