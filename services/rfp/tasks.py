"""Celery tasks for RFP intake (Phase 2b stub — graph attaches in Phase 3)."""

from __future__ import annotations

import logging

import config  # noqa: F401 — sys.path for data/pipelines
from celery_app import celery_app
from database import engine, ensure_schema
from sqlmodel import Session

from pipelines.rfp_intake.repository import get_ticket

logger = logging.getLogger(__name__)

TASK_NAME = "rfp.process_rfp"


@celery_app.task(bind=True, max_retries=3, name=TASK_NAME)
def process_rfp(self, ticket_id: str) -> dict:
    """Stub: load ticket and log. Phase 3 attaches the intake graph here.

    Does NOT change ticket status — stays ``analyzing`` until the graph advances
    it via ``update_ticket_status``.
    """
    ensure_schema()
    with Session(engine) as session:
        ticket = get_ticket(session, ticket_id)
        if ticket is None:
            raise ValueError(f"ticket not found: {ticket_id}")
        logger.info(
            "processing RFP ticket %s from %s",
            ticket.ticket_id,
            ticket.raw_pdf_path,
        )
        # TODO(Phase 3): invoke intake graph; status advances only via repository choke-point.
        return {"ticket_id": ticket.ticket_id, "status": ticket.status}
