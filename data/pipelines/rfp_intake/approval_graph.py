"""Per-department RFP approval LangGraph — approve → regen → END.

One graph instance serves one department on
``thread_id = f"rfp-{ticket_id}:{department}"``. Ticket-level extract, §7
arbitration, CEO gate, and synthesis live in ``approval_orchestration`` (P3 driver).

DB-pure: no Session/repository. Compile WITH a checkpointer per operation::

    with checkpointer_cm() as saver:  # or InMemorySaver in tests
        graph = build_dept_approval_graph(saver)
        result = graph.invoke(initial, {"configurable": {"thread_id": thread_id}})

Separate ``regen`` node (no in-node interrupt loop). Reject stamps ``needs_regen``;
regen runs ``generate_json`` and returns updated ``section`` so the draft is durable.

P3 contracts:
- Read pending interrupts from the invoke ``__interrupt__`` return, never get_state.
- After reject, collect the new interrupt from that invoke (re-invoke if empty).
- ``thread_id = f"rfp-{ticket_id}:{department}"`` (CEO uses ``:ceo`` in orchestration).
- Driver owns Postgres persistence; SQLite holds pause/resume only.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from pipelines.rfp_intake.generation import generate_json
from pipelines.rfp_intake.graph import DEPARTMENT_OWNERS
from pipelines.rfp_intake.response_evaluators import ITERATION_LIMIT

logger = logging.getLogger(__name__)

_EXTRACT_KEYS = ("cost", "setup_days", "price_per_cover")


class DeptApprovalState(TypedDict, total=False):
    """Single-department approval state (one section; no fan-in reducers)."""

    department: str
    section: dict
    rework_count: int
    outcome: str | None
    error: str | None


def _null_numbers() -> dict[str, None]:
    return {"cost": None, "setup_days": None, "price_per_cover": None}


def _coerce_extract(parsed: dict[str, Any]) -> dict[str, Any]:
    out = _null_numbers()
    for key in _EXTRACT_KEYS:
        raw = parsed.get(key)
        if raw is None:
            continue
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            out[key] = float(raw)
            continue
        try:
            out[key] = float(str(raw).strip())
        except (TypeError, ValueError):
            out[key] = None
    return out


def approve_node(state: DeptApprovalState) -> dict[str, Any]:
    """Interrupt-first approve — no LLM in this node."""
    department = str(state.get("department") or "")
    section = dict(state.get("section") or {})
    rework_count = int(state.get("rework_count") or 0)

    decision = interrupt(
        {
            "department": department,
            "draft": section.get("draft_content"),
            "cost": section.get("cost"),
            "setup_days": section.get("setup_days"),
            "price_per_cover": section.get("price_per_cover"),
            "forced_request_changes": bool(section.get("forced_request_changes")),
            "arbiter_feedback": section.get("arbiter_feedback"),
            "rework_count": rework_count,
        }
    )

    action = decision
    human_feedback = None
    if isinstance(decision, dict):
        action = decision.get("action") or decision.get("decision") or decision
        if decision.get("feedback"):
            human_feedback = str(decision.get("feedback"))

    if action == "approve":
        return {"outcome": "approved", "section": section}

    if action in ("reject", "request_changes"):
        if rework_count >= ITERATION_LIMIT:
            return {"outcome": "exhausted", "section": section}
        stamped = dict(section)
        stamped["needs_regen"] = True
        if human_feedback:
            stamped["human_feedback"] = human_feedback
        return {"section": stamped}

    return {
        "outcome": f"unknown:{action!r}",
        "section": section,
        "error": f"unknown approval decision: {action!r}",
    }


def regen_node(state: DeptApprovalState) -> dict[str, Any]:
    """Separate regen node — durable section update via generate_json."""
    department = str(state.get("department") or "")
    section = dict(state.get("section") or {})
    rework_count = int(state.get("rework_count") or 0) + 1
    owner = DEPARTMENT_OWNERS.get(department, department)
    feedback_parts = [
        str(section.get("arbiter_feedback") or "").strip(),
        str(section.get("human_feedback") or "").strip(),
    ]
    feedback = "\n".join(p for p in feedback_parts if p)

    system_prompt = (
        f"You revise the {department} department proposal section for Brasaland "
        f"(owner: {owner}). Address the feedback. Never invent absent figures — "
        "use null when a number is not stated. Respond with JSON only: "
        '{"draft_content": str, "cost": number|null, "setup_days": number|null, '
        '"price_per_cover": number|null}.'
    )
    user_prompt = (
        f"Prior draft:\n{section.get('draft_content') or ''}\n\n"
        f"Feedback to address:\n{feedback or '(none)'}"
    )
    try:
        parsed = generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2048,
        )
        if not isinstance(parsed, dict):
            parsed = {}
        draft = str(parsed.get("draft_content") or "").strip()
        numbers = _coerce_extract(parsed)
    except Exception as exc:  # noqa: BLE001 — soft-fail regen
        logger.warning(
            "dept approval regen %s failed: %s",
            department,
            type(exc).__name__,
        )
        draft = str(section.get("draft_content") or "")
        numbers = _null_numbers()

    if not draft:
        draft = str(section.get("draft_content") or "")

    merged = dict(section)
    merged["draft_content"] = draft
    merged.update(numbers)
    merged.pop("needs_regen", None)
    merged.pop("forced_request_changes", None)
    return {"section": merged, "rework_count": rework_count}


def route_after_approve(state: DeptApprovalState) -> str:
    if state.get("outcome"):
        return END
    if (state.get("section") or {}).get("needs_regen"):
        return "regen"
    return END


def build_dept_approval_graph(checkpointer: Any) -> Any:
    """Compile the per-dept approval graph WITH the provided checkpointer."""
    if checkpointer is None:
        raise ValueError("build_dept_approval_graph requires a checkpointer")

    builder: StateGraph = StateGraph(DeptApprovalState)
    builder.add_node("approve", approve_node)
    builder.add_node("regen", regen_node)
    builder.add_edge(START, "approve")
    builder.add_conditional_edges(
        "approve",
        route_after_approve,
        {"regen": "regen", END: END},
    )
    builder.add_edge("regen", "approve")
    return builder.compile(checkpointer=checkpointer)
