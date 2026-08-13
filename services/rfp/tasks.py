"""Celery tasks for RFP intake - runs the graph, persists, advances status."""

from __future__ import annotations

import logging
import traceback

import config  # noqa: F401 - sys.path for data/pipelines
from celery_app import celery_app
from database import engine, ensure_schema
from sqlmodel import Session

from pipelines.rfp_intake.graph import run_intake
from pipelines.rfp_intake.repository import (
    get_department_sections,
    get_rfp_metadata,
    get_ticket,
    save_department_sections,
    save_rfp_metadata,
    update_department_section,
    update_ticket_status,
    merge_evaluation_results,
)
from pipelines.rfp_intake.response_graph import run_response
from pipelines.rfp_intake.approval_orchestration import (
    apply_arbitration_stamps,
    extract_all_sections,
)
from pipelines.rfp_intake.arbitration import run_arbitration
from pipelines.rfp_intake.approval_graph import build_dept_approval_graph
from checkpointer import checkpointer_cm
from approval_driver import dept_thread_id, first_interrupt_id

logger = logging.getLogger(__name__)

TASK_NAME = "rfp.process_rfp"
TASK_NAME_RESPONSE = "rfp.process_rfp_response"
TASK_NAME_APPROVAL = "rfp.process_rfp_approval"


@celery_app.task(bind=True, max_retries=3, name=TASK_NAME)
def process_rfp(self, ticket_id: str) -> dict:
    """Run intake graph for a ticket; persist results; advance status via choke-point.

    ``status="analyzing"`` is set only in ``create_ticket``. This task advances via
    ``update_ticket_status`` to ``discarded`` or ``intake_complete``.
    """
    ensure_schema()
    with Session(engine) as session:
        ticket = get_ticket(session, ticket_id)
        if ticket is None:
            logger.error("RFP ticket not found: %s", ticket_id)
            return {"ticket_id": ticket_id, "status": "not_found"}

        logger.info(
            "RFP intake received ticket_id=%s rfp_id=%s path=%s",
            ticket.ticket_id,
            ticket.rfp_id,
            ticket.raw_pdf_path,
        )

        try:
            state = run_intake(
                ticket_id=ticket.ticket_id,
                rfp_id=ticket.rfp_id,
                raw_pdf_path=ticket.raw_pdf_path,
            )
        except Exception as exc:  # noqa: BLE001 - never leave ticket at analyzing
            logger.error(
                "RFP intake crashed ticket_id=%s: %s\n%s",
                ticket_id,
                type(exc).__name__,
                traceback.format_exc(),
            )
            update_ticket_status(session, ticket_id, "discarded")
            return {
                "ticket_id": ticket_id,
                "status": "discarded",
                "reason": f"intake failed: {type(exc).__name__}",
            }

        logger.info("RFP intake graph done ticket_id=%s", ticket_id)

        if state.get("is_valid_rfp") is False:
            reason = state.get("discard_reason")
            logger.info(
                "RFP intake discarded ticket_id=%s reason=%s",
                ticket_id,
                reason,
            )
            update_ticket_status(session, ticket_id, "discarded")
            return {
                "ticket_id": ticket_id,
                "status": "discarded",
                "reason": reason,
            }

        metadata = state.get("metadata") or {}
        sections = state.get("department_sections") or []
        summary = state.get("summary")

        save_rfp_metadata(session, rfp_id=ticket.rfp_id, metadata=metadata)
        save_department_sections(
            session,
            ticket_id=ticket.ticket_id,
            sections=sections,
        )
        update_ticket_status(session, ticket_id, "intake_complete")

        logger.info(
            "RFP intake_complete ticket_id=%s departments=%s summary=%s",
            ticket_id,
            state.get("departments_needed"),
            summary,
        )
        return {
            "ticket_id": ticket_id,
            "status": "intake_complete",
            "departments": state.get("departments_needed"),
            "summary": summary,
        }


@celery_app.task(bind=True, max_retries=3, name=TASK_NAME_RESPONSE)
def process_rfp_response(self, ticket_id: str) -> dict:
    """Run response graph; persist drafts/evaluations; land at under_evaluation.

    Crash path (never discard, never stay drafting): best-effort needs_human_review
    on known departments, then always advance to ``under_evaluation``.
    """
    ensure_schema()
    with Session(engine) as session:
        ticket = get_ticket(session, ticket_id)
        if ticket is None:
            logger.error("RFP response ticket not found: %s", ticket_id)
            return {"ticket_id": ticket_id, "status": "not_found"}

        logger.info(
            "RFP response received ticket_id=%s rfp_id=%s status=%s",
            ticket.ticket_id,
            ticket.rfp_id,
            ticket.status,
        )

        departments_needed: list[str] = []
        try:
            update_ticket_status(session, ticket_id, "drafting")

            metadata_row = get_rfp_metadata(session, ticket.rfp_id)
            if metadata_row is None:
                raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")

            departments_needed = [
                str(d) for d in (metadata_row.departments_needed or [])
            ]
            metadata = {
                "client_name": metadata_row.client_name,
                "location": metadata_row.location,
                "service_type": metadata_row.service_type,
                "scope": metadata_row.scope,
                "deadline": metadata_row.deadline,
                "budget_range": metadata_row.budget_range,
                "open_questions": metadata_row.open_questions,
            }

            section_rows = get_department_sections(session, ticket_id)
            input_sections = [
                {
                    "department_id": row.department_id,
                    "key_aspects": row.key_aspects,
                }
                for row in section_rows
            ]

            result = run_response(
                ticket_id=ticket.ticket_id,
                rfp_id=ticket.rfp_id,
                metadata=metadata,
                departments_needed=departments_needed,
                input_sections=input_sections,
            )

            for sec in result.get("department_sections") or []:
                update_department_section(
                    session,
                    ticket_id=ticket_id,
                    department_id=str(sec["department_id"]),
                    draft_content=str(sec.get("draft_content") or ""),
                    evaluation_results=dict(sec.get("evaluation_results") or {}),
                )

            update_ticket_status(session, ticket_id, "under_evaluation")
            logger.info(
                "RFP under_evaluation ticket_id=%s departments=%s",
                ticket_id,
                departments_needed,
            )
            return {
                "ticket_id": ticket_id,
                "status": "under_evaluation",
                "departments": departments_needed,
            }
        except Exception as exc:  # noqa: BLE001 — never leave at drafting / never discard
            logger.error(
                "RFP response crashed ticket_id=%s: %s\n%s",
                ticket_id,
                type(exc).__name__,
                traceback.format_exc(),
            )
            review = {
                "overall_pass": False,
                "exhausted": True,
                "needs_human_review": True,
                "error": str(exc),
                "iterations": 0,
            }
            for department_id in departments_needed:
                try:
                    update_department_section(
                        session,
                        ticket_id=ticket_id,
                        department_id=str(department_id),
                        draft_content="",
                        evaluation_results=review,
                    )
                except Exception:  # noqa: BLE001 — best-effort per row
                    logger.warning(
                        "RFP response crash recovery skip dept=%s ticket_id=%s",
                        department_id,
                        ticket_id,
                    )
            try:
                update_ticket_status(session, ticket_id, "under_evaluation")
            except Exception:  # noqa: BLE001 — never re-raise into Celery retries
                logger.exception(
                    "RFP response crash recovery failed to set under_evaluation "
                    "ticket_id=%s",
                    ticket_id,
                )
            return {
                "ticket_id": ticket_id,
                "status": "under_evaluation",
                "reason": f"response failed: {type(exc).__name__}",
            }


@celery_app.task(bind=True, max_retries=3, name=TASK_NAME_APPROVAL)
def process_rfp_approval(self, ticket_id: str) -> dict:
    """Pre-pass + start per-dept approval threads; land at waiting_for_approval.

    Crash before status flip → stay under_evaluation + needs_human_review flags.
    Crash after → stay waiting_for_approval; never advance to done.
    """
    ensure_schema()
    with Session(engine) as session:
        ticket = get_ticket(session, ticket_id)
        if ticket is None:
            logger.error("RFP approval ticket not found: %s", ticket_id)
            return {"ticket_id": ticket_id, "status": "not_found"}

        logger.info(
            "RFP approval received ticket_id=%s rfp_id=%s status=%s",
            ticket.ticket_id,
            ticket.rfp_id,
            ticket.status,
        )

        departments_needed: list[str] = []
        flipped = False
        try:
            if ticket.status != "under_evaluation":
                raise ValueError(
                    f"ticket must be under_evaluation to start approval "
                    f"(current status: {ticket.status})"
                )

            metadata_row = get_rfp_metadata(session, ticket.rfp_id)
            if metadata_row is None:
                raise ValueError(f"rfp_metadata not found for rfp_id={ticket.rfp_id}")

            departments_needed = [
                str(d) for d in (metadata_row.departments_needed or [])
            ]
            metadata = {
                "client_name": metadata_row.client_name,
                "location": metadata_row.location,
                "service_type": metadata_row.service_type,
                "scope": metadata_row.scope,
                "deadline": metadata_row.deadline,
                "budget_range": metadata_row.budget_range,
                "open_questions": metadata_row.open_questions,
            }

            section_rows = get_department_sections(session, ticket_id)
            sections: dict[str, dict] = {}
            for row in section_rows:
                dept = str(row.department_id)
                if dept not in departments_needed:
                    continue
                eval_results = dict(row.evaluation_results or {})
                sections[dept] = {
                    "draft_content": row.draft_content,
                    "key_aspects": row.key_aspects,
                    "evaluation_results": eval_results,
                    "cost": eval_results.get("cost"),
                    "setup_days": eval_results.get("setup_days"),
                    "price_per_cover": eval_results.get("price_per_cover"),
                }

            numbers = extract_all_sections(sections, departments_needed, metadata)
            for dept, nums in numbers.items():
                merge_evaluation_results(
                    session,
                    ticket_id=ticket_id,
                    department_id=dept,
                    patch=dict(nums),
                )
                sections[dept] = {**sections.get(dept, {}), **dict(nums)}

            arb_raw = run_arbitration(sections=sections, metadata=metadata)
            stamped, arbitration = apply_arbitration_stamps(sections, arb_raw)

            for dept in departments_needed:
                sec = stamped.get(dept) or {}
                stamp_patch: dict = {
                    "arbitration": arbitration,
                }
                if sec.get("forced_request_changes") is not None:
                    stamp_patch["forced_request_changes"] = sec.get(
                        "forced_request_changes"
                    )
                if sec.get("arbiter_feedback") is not None:
                    stamp_patch["arbiter_feedback"] = sec.get("arbiter_feedback")
                for key in ("cost", "setup_days", "price_per_cover"):
                    if key in sec:
                        stamp_patch[key] = sec.get(key)
                merge_evaluation_results(
                    session,
                    ticket_id=ticket_id,
                    department_id=dept,
                    patch=stamp_patch,
                )
                sections[dept] = {
                    **(sections.get(dept) or {}),
                    **{k: v for k, v in stamp_patch.items() if k != "arbitration"},
                    "arbitration": arbitration,
                }

            update_ticket_status(session, ticket_id, "waiting_for_approval")
            flipped = True

            with checkpointer_cm() as saver:
                graph = build_dept_approval_graph(saver)
                for dept in departments_needed:
                    sec = dict(sections.get(dept) or {})
                    result = graph.invoke(
                        {
                            "department": dept,
                            "section": sec,
                            "rework_count": 0,
                            "outcome": None,
                        },
                        {
                            "configurable": {
                                "thread_id": dept_thread_id(ticket_id, dept)
                            }
                        },
                    )
                    interrupt_id = first_interrupt_id(result)
                    if not interrupt_id:
                        raise RuntimeError(
                            f"no __interrupt__ after start for department={dept}"
                        )
                    merge_evaluation_results(
                        session,
                        ticket_id=ticket_id,
                        department_id=dept,
                        patch={"interrupt_id": interrupt_id},
                    )

            logger.info(
                "RFP waiting_for_approval ticket_id=%s departments=%s",
                ticket_id,
                departments_needed,
            )
            return {
                "ticket_id": ticket_id,
                "status": "waiting_for_approval",
                "departments": departments_needed,
            }
        except Exception as exc:  # noqa: BLE001 — never leave stuck / never done
            logger.error(
                "RFP approval crashed ticket_id=%s flipped=%s: %s\n%s",
                ticket_id,
                flipped,
                type(exc).__name__,
                traceback.format_exc(),
            )
            flag = {
                "needs_human_review": True,
                "error": str(exc),
                "approval_error": type(exc).__name__,
            }
            for department_id in departments_needed:
                try:
                    merge_evaluation_results(
                        session,
                        ticket_id=ticket_id,
                        department_id=str(department_id),
                        patch=flag,
                    )
                except Exception:  # noqa: BLE001 — best-effort
                    logger.warning(
                        "RFP approval crash recovery skip dept=%s ticket_id=%s",
                        department_id,
                        ticket_id,
                    )
            if not flipped:
                return {
                    "ticket_id": ticket_id,
                    "status": "under_evaluation",
                    "reason": f"approval failed: {type(exc).__name__}",
                }
            return {
                "ticket_id": ticket_id,
                "status": "waiting_for_approval",
                "reason": f"approval failed: {type(exc).__name__}",
            }

