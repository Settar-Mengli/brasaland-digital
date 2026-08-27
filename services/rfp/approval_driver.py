"""P3 approval driver helpers — finalize / thread ids (DB I/O via repository)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from langgraph.types import Command
from sqlmodel import Session

from checkpointer import checkpointer_cm
from pipelines.rfp_intake.approval_graph import build_dept_approval_graph
from pipelines.rfp_intake.approval_orchestration import (
    build_ceo_interrupt_graph,
    synthesize_final_document,
)
from pipelines.rfp_intake.graph import DEPARTMENT_OWNERS
from pipelines.rfp_intake.response_evaluators import evaluate_all
from pipelines.rfp_intake.repository import (
    get_department_sections,
    get_rfp_metadata,
    get_ticket,
    merge_evaluation_results,
    save_final_document,
    update_department_section,
    update_department_section_approval,
    update_ticket_status,
)

logger = logging.getLogger(__name__)

INTERRUPT_KEY = "__interrupt__"
_TRACE_MAX = 20


def dept_thread_id(ticket_id: str, department: str) -> str:
    return f"rfp-{ticket_id}:{department}"


def bounded_trace(result: Any, *, existing: list[Any] | None = None) -> list[dict]:
    """Prefer full graph-state ``trace`` (already accumulated); else keep prior.

    Graph nodes append via ``operator.add``, so ``result["trace"]`` is the
    complete ordered history for the thread. Do not concatenate prior DB rows
    onto that list (would duplicate). Cap at ``_TRACE_MAX``.
    """
    fresh: list[dict] = []
    if isinstance(result, dict):
        for entry in result.get("trace") or []:
            if isinstance(entry, dict):
                fresh.append(entry)
    if fresh:
        return fresh[-_TRACE_MAX:]
    prior = [e for e in (existing or []) if isinstance(e, dict)]
    return prior[-_TRACE_MAX:]


def ceo_thread_id(ticket_id: str) -> str:
    return f"rfp-{ticket_id}:ceo"


def _as_interrupt_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    return [raw]


def interrupts_from_result(result: Any) -> list[Any]:
    if not isinstance(result, dict):
        return []
    return _as_interrupt_list(result.get(INTERRUPT_KEY))


def first_interrupt_id(result: Any) -> str | None:
    pending = interrupts_from_result(result)
    if not pending:
        return None
    item_id = getattr(pending[0], "id", None)
    return str(item_id) if item_id else None


def resume_value_for_decision(action: str, feedback: str | None) -> Any:
    """Match approve_node contract: string action, or dict when feedback is set.

    ``approve_node`` treats a plain string as the action, and a dict as
    ``{action|decision, feedback?}`` (feedback → section.human_feedback → regen).
    """
    if feedback:
        return {"action": action, "feedback": feedback}
    return action


def _metadata_dict(metadata_row: Any) -> dict[str, Any]:
    return {
        "client_name": metadata_row.client_name,
        "location": metadata_row.location,
        "service_type": metadata_row.service_type,
        "scope": metadata_row.scope,
        "deadline": metadata_row.deadline,
        "budget_range": metadata_row.budget_range,
        "open_questions": metadata_row.open_questions,
    }


def _sections_map(rows: list[Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        eval_results = dict(row.evaluation_results or {})
        out[str(row.department_id)] = {
            "draft_content": row.draft_content,
            "key_aspects": row.key_aspects,
            "evaluation_results": eval_results,
            "cost": eval_results.get("cost"),
            "setup_days": eval_results.get("setup_days"),
            "price_per_cover": eval_results.get("price_per_cover"),
            "forced_request_changes": eval_results.get("forced_request_changes"),
            "arbiter_feedback": eval_results.get("arbiter_feedback"),
            "human_feedback": eval_results.get("human_feedback"),
        }
    return out


def _arbitration_from_sections(rows: list[Any]) -> dict[str, Any]:
    for row in rows:
        eval_results = dict(row.evaluation_results or {})
        arb = eval_results.get("arbitration")
        if isinstance(arb, dict):
            return dict(arb)
    return {}


def dept_is_terminal(row: Any) -> bool:
    """Approved, or rejected with graph_outcome exhausted."""
    if row.approval_status == "approved":
        return True
    if row.approval_status == "rejected":
        eval_results = dict(row.evaluation_results or {})
        return eval_results.get("graph_outcome") == "exhausted"
    return False


def all_active_depts_terminal(
    rows: list[Any], departments_needed: list[str]
) -> bool:
    by_dept = {str(r.department_id): r for r in rows}
    for dept in departments_needed:
        row = by_dept.get(str(dept))
        if row is None or not dept_is_terminal(row):
            return False
    return True


def _persist_arbitration_patch(
    session: Session,
    *,
    ticket_id: str,
    departments_needed: list[str],
    patch: dict[str, Any],
) -> None:
    rows = get_department_sections(session, ticket_id)
    by_dept = {str(r.department_id): r for r in rows}
    for dept in departments_needed:
        row = by_dept.get(str(dept))
        if row is None:
            continue
        eval_results = dict(row.evaluation_results or {})
        arb = dict(eval_results.get("arbitration") or {})
        arb.update(patch)
        merge_evaluation_results(
            session,
            ticket_id=ticket_id,
            department_id=str(dept),
            patch={"arbitration": arb},
        )


def _approval_outcomes_from_rows(rows: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "department_id": row.department_id,
                "status": row.approval_status,
                "approver": row.approver,
                "approved_at": (
                    row.approved_at.isoformat() if row.approved_at else None
                ),
            }
        )
    return out


def synthesize_and_complete(
    session: Session,
    *,
    ticket_id: str,
) -> dict[str, Any]:
    """Build FinalDocument, save it, advance ticket to done."""
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"ticket not found: {ticket_id}")
    metadata_row = get_rfp_metadata(session, ticket.rfp_id)
    if metadata_row is None:
        raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")
    departments_needed = [str(d) for d in (metadata_row.departments_needed or [])]
    rows = get_department_sections(session, ticket_id)
    sections = _sections_map(rows)
    arbitration = _arbitration_from_sections(rows)
    ceo_decision = arbitration.get("ceo_decision")
    ceo_approved_at = arbitration.get("ceo_approved_at")

    payload = synthesize_final_document(
        ticket_id=ticket_id,
        sections=sections,
        metadata=_metadata_dict(metadata_row),
        arbitration=arbitration,
        ceo_decision=ceo_decision,
        departments_needed=departments_needed,
        ceo_approved_at=ceo_approved_at,
        approval_outcomes=_approval_outcomes_from_rows(rows),
        error=None,
    )
    if payload is None:
        raise ValueError("synthesize_final_document returned None")

    save_final_document(
        session,
        ticket_id=ticket_id,
        sections=list(payload.get("sections") or []),
        total_estimated_value=payload.get("total_estimated_value"),
        document=payload,
    )
    update_ticket_status(session, ticket_id, "done")
    return {
        "status": "done",
        "final_document": payload,
        "ceo_pending": False,
    }


def maybe_finalize_ticket(session: Session, ticket_id: str) -> dict[str, Any]:
    """If all active depts terminal: start CEO interrupt or synthesize→done."""
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"ticket not found: {ticket_id}")
    metadata_row = get_rfp_metadata(session, ticket.rfp_id)
    if metadata_row is None:
        raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")
    departments_needed = [str(d) for d in (metadata_row.departments_needed or [])]
    rows = get_department_sections(session, ticket_id)

    if not all_active_depts_terminal(rows, departments_needed):
        return {"status": ticket.status, "ceo_pending": False, "finalized": False}

    arbitration = _arbitration_from_sections(rows)
    ceo_required = bool(arbitration.get("ceo_approval_required"))
    ceo_decision = arbitration.get("ceo_decision")

    if ceo_required and ceo_decision != "approved":
        if ceo_decision == "rejected":
            return {
                "status": ticket.status,
                "ceo_pending": False,
                "finalized": False,
                "ceo_decision": "rejected",
            }
        if arbitration.get("ceo_interrupt_id"):
            return {
                "status": ticket.status,
                "ceo_pending": True,
                "finalized": False,
            }

        with checkpointer_cm() as saver:
            graph = build_ceo_interrupt_graph(saver)
            result = graph.invoke(
                {
                    "ticket_id": ticket_id,
                    "arbitration": arbitration,
                    "ceo_decision": None,
                },
                {"configurable": {"thread_id": ceo_thread_id(ticket_id)}},
            )
        ceo_id = first_interrupt_id(result)
        if not ceo_id:
            raise RuntimeError("CEO interrupt graph did not return __interrupt__")
        _persist_arbitration_patch(
            session,
            ticket_id=ticket_id,
            departments_needed=departments_needed,
            patch={"ceo_interrupt_id": ceo_id},
        )
        return {
            "status": ticket.status,
            "ceo_pending": True,
            "finalized": False,
            "ceo_interrupt_id": ceo_id,
        }

    return {
        **synthesize_and_complete(session, ticket_id=ticket_id),
        "finalized": True,
    }


def serialize_final_document(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    if isinstance(row.document, dict) and row.document:
        return dict(row.document)
    return {
        "ticket_id": row.ticket_id,
        "sections": row.sections,
        "total_estimated_value": row.total_estimated_value,
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
    }


_NUMBER_KEYS = ("cost", "setup_days", "price_per_cover")

_FRESH_EVAL_KEYS = (
    "readability",
    "relevance",
    "compliance",
    "overall_pass",
    "feedback_for_generator",
    "ceo_approval_required",
    "department_id",
    "iterations",
    "exhausted",
    "needs_human_review",
)


def _coerce_key_aspects(raw: object) -> list[str]:
    """Null-safe coerce department_section.key_aspects to list[str] for evaluate_all."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return [raw] if raw.strip() else []
    if isinstance(raw, dict):
        return []
    if isinstance(raw, list):
        return [str(a) for a in raw if str(a).strip()]
    return [str(raw)] if str(raw).strip() else []


def _persist_regen_section(
    session: Session,
    *,
    ticket_id: str,
    department_id: str,
    section: dict[str, Any],
    interrupt_id: str,
    budget_range: str | None,
    graph_result: dict[str, Any] | None = None,
) -> None:
    """Read-merge-write draft + re-evaluated flags in ONE update_department_section."""
    rows = get_department_sections(session, ticket_id)
    by_dept = {str(r.department_id): r for r in rows}
    row = by_dept.get(str(department_id))
    if row is None:
        raise ValueError(
            f"department_section not found: ticket_id={ticket_id!r} "
            f"department_id={department_id!r}"
        )
    draft = str(section.get("draft_content") or row.draft_content or "")
    key_aspects = _coerce_key_aspects(row.key_aspects)
    fresh = evaluate_all(draft, key_aspects, budget_range, str(department_id))

    merged_eval = dict(row.evaluation_results or {})
    for key in _FRESH_EVAL_KEYS:
        if key in fresh:
            merged_eval[key] = fresh[key]
    for key in _NUMBER_KEYS:
        if key in section:
            merged_eval[key] = section.get(key)
    if "human_feedback" in section:
        merged_eval["human_feedback"] = section.get("human_feedback")
    if "arbiter_feedback" in section:
        merged_eval["arbiter_feedback"] = section.get("arbiter_feedback")
    if "forced_request_changes" in section:
        merged_eval["forced_request_changes"] = section.get("forced_request_changes")
    merged_eval.pop("needs_regen", None)
    merged_eval["interrupt_id"] = interrupt_id
    if graph_result is not None:
        prior = merged_eval.get("trace")
        prior_list = prior if isinstance(prior, list) else None
        merged_eval["trace"] = bounded_trace(graph_result, existing=prior_list)
    update_department_section(
        session,
        ticket_id=ticket_id,
        department_id=str(department_id),
        draft_content=draft,
        evaluation_results=merged_eval,
    )


def apply_section_decision(
    session: Session,
    *,
    ticket_id: str,
    department_id: str,
    action: str,
    feedback: str | None,
) -> dict[str, Any]:
    """Resume one dept thread; persist approve / regen / exhausted; maybe finalize."""
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise LookupError("ticket not found")
    if ticket.status != "waiting_for_approval":
        raise ValueError(
            "ticket must be waiting_for_approval to decide "
            f"(current status: {ticket.status})"
        )

    metadata_row = get_rfp_metadata(session, ticket.rfp_id)
    if metadata_row is None:
        raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")
    departments_needed = [str(d) for d in (metadata_row.departments_needed or [])]
    if str(department_id) not in departments_needed:
        raise ValueError(f"department {department_id!r} not in departments_needed")
    budget_range = metadata_row.budget_range
    if budget_range is not None:
        budget_range = str(budget_range)

    rows = get_department_sections(session, ticket_id)
    by_dept = {str(r.department_id): r for r in rows}
    row = by_dept.get(str(department_id))
    if row is None:
        raise ValueError(f"department_section not found for {department_id!r}")

    eval_results = dict(row.evaluation_results or {})
    interrupt_id = eval_results.get("interrupt_id")
    if not interrupt_id:
        raise ValueError("missing interrupt_id for department decision")

    if action not in ("approve", "reject", "request_changes"):
        raise ValueError(f"invalid action: {action!r}")

    resume_value = resume_value_for_decision(action, feedback)
    config = {
        "configurable": {"thread_id": dept_thread_id(ticket_id, str(department_id))}
    }

    with checkpointer_cm() as saver:
        graph = build_dept_approval_graph(saver)
        result = graph.invoke(
            Command(resume={str(interrupt_id): resume_value}),
            config,
        )
        pending = interrupts_from_result(result)
        if not pending and not result.get("outcome"):
            result = graph.invoke(None, config)
            pending = interrupts_from_result(result)

    prior_trace = eval_results.get("trace")
    prior_list = prior_trace if isinstance(prior_trace, list) else None
    trace_patch = {"trace": bounded_trace(result, existing=prior_list)}

    if pending:
        new_id = first_interrupt_id(result)
        if not new_id:
            raise RuntimeError("regen interrupt missing id")
        section = dict(result.get("section") or {})
        _persist_regen_section(
            session,
            ticket_id=ticket_id,
            department_id=str(department_id),
            section=section,
            interrupt_id=new_id,
            budget_range=budget_range,
            graph_result=result if isinstance(result, dict) else None,
        )
        return {
            "ticket_id": ticket_id,
            "department_id": department_id,
            "outcome": "pending_reapproval",
            "status": ticket.status,
            "ceo_pending": False,
            "final_document": None,
        }

    outcome = result.get("outcome")
    if outcome == "approved":
        update_department_section_approval(
            session,
            ticket_id=ticket_id,
            department_id=str(department_id),
            approval_status="approved",
            approver=DEPARTMENT_OWNERS.get(str(department_id), str(department_id)),
            approved_at=datetime.now(UTC),
        )
        merge_evaluation_results(
            session,
            ticket_id=ticket_id,
            department_id=str(department_id),
            patch={
                "interrupt_id": None,
                "graph_outcome": "approved",
                **trace_patch,
            },
        )
        fin = maybe_finalize_ticket(session, ticket_id)
        ticket = get_ticket(session, ticket_id)
        return {
            "ticket_id": ticket_id,
            "department_id": department_id,
            "outcome": "approved",
            "status": ticket.status if ticket else fin.get("status"),
            "ceo_pending": bool(fin.get("ceo_pending")),
            "final_document": fin.get("final_document"),
        }

    if outcome == "exhausted":
        update_department_section_approval(
            session,
            ticket_id=ticket_id,
            department_id=str(department_id),
            approval_status="rejected",
            approver=DEPARTMENT_OWNERS.get(str(department_id), str(department_id)),
            approved_at=datetime.now(UTC),
        )
        merge_evaluation_results(
            session,
            ticket_id=ticket_id,
            department_id=str(department_id),
            patch={
                "interrupt_id": None,
                "graph_outcome": "exhausted",
                **trace_patch,
            },
        )
        fin = maybe_finalize_ticket(session, ticket_id)
        ticket = get_ticket(session, ticket_id)
        return {
            "ticket_id": ticket_id,
            "department_id": department_id,
            "outcome": "exhausted",
            "status": ticket.status if ticket else fin.get("status"),
            "ceo_pending": bool(fin.get("ceo_pending")),
            "final_document": fin.get("final_document"),
        }

    raise RuntimeError(f"unexpected approval outcome: {outcome!r}")


def apply_ceo_decision(
    session: Session,
    *,
    ticket_id: str,
    action: str,
) -> dict[str, Any]:
    """Resume CEO thread; approve → synthesize→done; reject → stay waiting."""
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise LookupError("ticket not found")
    if ticket.status != "waiting_for_approval":
        raise ValueError(
            "ticket must be waiting_for_approval for CEO decision "
            f"(current status: {ticket.status})"
        )

    metadata_row = get_rfp_metadata(session, ticket.rfp_id)
    if metadata_row is None:
        raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")
    departments_needed = [str(d) for d in (metadata_row.departments_needed or [])]
    rows = get_department_sections(session, ticket_id)
    arbitration = _arbitration_from_sections(rows)

    if not arbitration.get("ceo_approval_required"):
        raise ValueError("ceo_approval_required is false for this ticket")
    ceo_interrupt_id = arbitration.get("ceo_interrupt_id")
    if not ceo_interrupt_id:
        raise ValueError("missing ceo_interrupt_id")

    if action not in ("approve", "reject"):
        raise ValueError(f"invalid CEO action: {action!r}")

    resume_value = resume_value_for_decision(action, None)
    config = {"configurable": {"thread_id": ceo_thread_id(ticket_id)}}

    with checkpointer_cm() as saver:
        graph = build_ceo_interrupt_graph(saver)
        result = graph.invoke(
            Command(resume={str(ceo_interrupt_id): resume_value}),
            config,
        )

    ceo_decision = result.get("ceo_decision")
    if ceo_decision == "approved":
        patch = {
            "ceo_decision": "approved",
            "ceo_approved_at": result.get("ceo_approved_at")
            or datetime.now(UTC).isoformat(),
            "ceo_interrupt_id": None,
        }
        _persist_arbitration_patch(
            session,
            ticket_id=ticket_id,
            departments_needed=departments_needed,
            patch=patch,
        )
        fin = synthesize_and_complete(session, ticket_id=ticket_id)
        return {
            "ticket_id": ticket_id,
            "ceo_decision": "approved",
            "status": "done",
            "final_document": fin.get("final_document"),
        }

    _persist_arbitration_patch(
        session,
        ticket_id=ticket_id,
        departments_needed=departments_needed,
        patch={
            "ceo_decision": "rejected",
            "ceo_interrupt_id": None,
        },
    )
    return {
        "ticket_id": ticket_id,
        "ceo_decision": "rejected",
        "status": "waiting_for_approval",
        "final_document": None,
    }
