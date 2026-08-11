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
    get_ticket,
    save_department_sections,
    save_rfp_metadata,
    update_ticket_status,
)

logger = logging.getLogger(__name__)

TASK_NAME = "rfp.process_rfp"


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

