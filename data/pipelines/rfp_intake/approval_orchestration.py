"""Ticket-level RFP approval orchestration — DB-pure helpers (not a mega-graph).

P3 driver sequence (driver owns all DB I/O)::

    1. Load sections + metadata from Postgres.
    2. extract_all_sections → persist number patches (merge_evaluation_results).
    3. run_arbitration → apply_arbitration_stamps → persist stamps.
    4. Spawn per-dept threads: thread_id = f"rfp-{ticket_id}:{department}"
       with build_dept_approval_graph(checkpointer) from approval_graph.
    5. Resume each dept thread on human decision (map-form Command(resume={{id: value}})).
    6. When all depts done: if ceo_approval_required, CEO graph on
       thread_id = f"rfp-{ticket_id}:ceo".
    7. synthesize_final_document → save_final_document.

P3 contracts:
- Read pending from invoke ``__interrupt__``, never get_state.
- After reject, collect the new interrupt (re-invoke if empty).
- thread_id encodes department (and ``:ceo``); map-form resume still needs interrupt id.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from pipelines.rfp_intake.generation import generate_json
from pipelines.rfp_intake.graph import ALL_DEPARTMENTS, DEPARTMENT_OWNERS

logger = logging.getLogger(__name__)

_CEO_NAME = "Mariana Restrepo"
_EXTRACT_KEYS = ("cost", "setup_days", "price_per_cover")


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


def extract_section_numbers(
    department: str,
    section: dict[str, Any],
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Extract cost / setup_days / price_per_cover for one section (never invent)."""
    _ = metadata  # reserved for future prompt context
    owner = DEPARTMENT_OWNERS.get(department, department)
    draft = str(section.get("draft_content") or "")
    key_aspects = section.get("key_aspects") or []

    system_prompt = (
        f"You extract structured numbers from the {department} department "
        f"proposal section for Brasaland (owner: {owner}). "
        "Never invent absent figures — use null when a number is not stated. "
        "Respond with JSON only: "
        '{"cost": number|null, "setup_days": number|null, '
        '"price_per_cover": number|null}. '
        "cost = this section's economic/cost estimate if stated. "
        "setup_days = promised setup/delivery business days if stated. "
        "price_per_cover = implied per-cover price if stated "
        "(primarily operaciones; others usually null)."
    )
    user_prompt = (
        f"Department: {department}\n"
        f"Key aspects:\n{key_aspects}\n\n"
        f"Draft content:\n{draft}"
    )
    try:
        parsed = generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=256,
        )
        return _coerce_extract(parsed if isinstance(parsed, dict) else {})
    except Exception as exc:  # noqa: BLE001 — soft-fail extract
        logger.warning(
            "approval extract %s failed: %s",
            department,
            type(exc).__name__,
        )
        return _null_numbers()


def extract_all_sections(
    sections: dict[str, dict],
    departments_needed: list[str],
    metadata: dict | None = None,
) -> dict[str, dict[str, Any]]:
    """Sequential extract over active departments. Returns {dept: numbers}."""
    out: dict[str, dict[str, Any]] = {}
    for department in departments_needed:
        sec = sections.get(department) or {}
        out[str(department)] = extract_section_numbers(
            str(department), dict(sec), metadata
        )
    return out


def apply_arbitration_stamps(
    sections: dict[str, dict],
    arbitration_result: dict[str, Any],
) -> tuple[dict[str, dict], dict[str, Any]]:
    """Merge arbiter section_stamps onto sections; return (sections, arbitration).

    ``arbitration_result`` is the dict from ``run_arbitration`` (may include
    ``section_stamps``). Stamps are removed from the returned arbitration record.
    """
    result = dict(arbitration_result or {})
    stamps = dict(result.pop("section_stamps", {}) or {})
    merged: dict[str, dict] = {
        str(dept): dict(payload or {}) for dept, payload in (sections or {}).items()
    }
    for dept, stamp in stamps.items():
        key = str(dept)
        base = dict(merged.get(key) or {})
        base.update(dict(stamp or {}))
        merged[key] = base
    return merged, result


class CeoInterruptState(TypedDict, total=False):
    ticket_id: str
    arbitration: dict | None
    ceo_decision: str | None
    ceo_approved_at: str | None
    error: str | None


def _ceo_interrupt_node(state: CeoInterruptState) -> dict[str, Any]:
    decision = interrupt(
        {
            "role": "ceo",
            "approver": _CEO_NAME,
            "ticket_id": state.get("ticket_id"),
            "arbitration": state.get("arbitration"),
        }
    )
    action = decision
    if isinstance(decision, dict):
        action = decision.get("action") or decision.get("decision") or decision
    if action in ("approve", "approved"):
        return {
            "ceo_decision": "approved",
            "ceo_approved_at": datetime.now(UTC).isoformat(),
        }
    return {
        "ceo_decision": "rejected",
        "error": "CEO rejected the proposal",
    }


def build_ceo_interrupt_graph(checkpointer: Any) -> Any:
    """Tiny one-node CEO interrupt graph. Thread: ``rfp-{ticket_id}:ceo``."""
    if checkpointer is None:
        raise ValueError("build_ceo_interrupt_graph requires a checkpointer")

    builder: StateGraph = StateGraph(CeoInterruptState)
    builder.add_node("ceo_interrupt", _ceo_interrupt_node)
    builder.add_edge(START, "ceo_interrupt")
    builder.add_edge("ceo_interrupt", END)
    return builder.compile(checkpointer=checkpointer)


def _format_total_estimated_value(budget_range: Any) -> str | None:
    if budget_range is None:
        return None
    text = str(budget_range).strip()
    if not text:
        return None
    return text


def synthesize_final_document(
    *,
    ticket_id: str,
    sections: dict[str, dict],
    metadata: dict | None,
    arbitration: dict | None,
    ceo_decision: str | None,
    departments_needed: list[str] | None = None,
    ceo_approved_at: str | None = None,
    approval_outcomes: list[dict] | None = None,
    error: str | None = None,
) -> dict[str, Any] | None:
    """Build FinalDocument payload per CONTEXT §2.4. No DB I/O."""
    if error or ceo_decision == "rejected":
        return None

    meta = dict(metadata or {})
    needed = list(departments_needed or [])
    if not needed:
        needed = [d for d in ALL_DEPARTMENTS if d in (sections or {})]

    outcomes = {
        str(o.get("department_id")): o
        for o in (approval_outcomes or [])
        if isinstance(o, dict) and o.get("department_id")
    }
    arb = arbitration or {}

    doc_sections: list[dict[str, Any]] = []
    for dept in ALL_DEPARTMENTS:
        if dept not in needed:
            continue
        sec = (sections or {}).get(dept) or {}
        outcome = outcomes.get(dept) or {}
        owner = DEPARTMENT_OWNERS.get(dept, dept)
        approved_at = outcome.get("approved_at")
        stamp = f"approved by {owner} at {approved_at}" if approved_at else None
        doc_sections.append(
            {
                "department_id": dept,
                "owner": owner,
                "draft_content": sec.get("draft_content"),
                "approval_stamp": stamp,
                "approver": outcome.get("approver") or owner,
                "approved_at": approved_at,
            }
        )

    ceo_line = None
    if arb.get("ceo_approval_required") and ceo_decision == "approved":
        ceo_at = ceo_approved_at or datetime.now(UTC).isoformat()
        ceo_line = f"CEO approval: {_CEO_NAME}, {ceo_at}"

    budget_range = meta.get("budget_range")
    total = _format_total_estimated_value(budget_range)
    open_questions = list(meta.get("open_questions") or [])
    if total is None and not budget_range:
        if not any("budget" in str(q).lower() for q in open_questions):
            open_questions = list(open_questions) + ["budget_range unstated"]

    return {
        "header": {
            "client_name": meta.get("client_name"),
            "location": meta.get("location"),
            "service_type": meta.get("service_type"),
            "generated_at": datetime.now(UTC).isoformat(),
            "ticket_id": ticket_id,
        },
        "sections": doc_sections,
        "arbitration_outcomes": {
            "triggers_fired": arb.get("triggers_fired") or [],
            "resolutions": arb.get("resolutions") or [],
        },
        "ceo_line": ceo_line,
        "total_estimated_value": total,
        "open_questions": open_questions,
    }
