"""Atomic ticket create and status updates for RFP intake."""

from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select

from pipelines.rfp_intake.lifecycle import validate_transition
from pipelines.rfp_intake.models import Ticket


def create_ticket(
    session: Session,
    *,
    rfp_id: str,
    content_hash: str,
    raw_pdf_path: str,
) -> tuple[Ticket, bool]:
    """Insert a ticket at status analyzing, or return the existing row on hash collide.

    This is the single place status is initialized to ``analyzing``.
    Idempotent on ``content_hash`` (re-upload returns the existing ticket).
    """
    ticket_id = str(uuid4())
    now = datetime.now(UTC)
    values = {
        "ticket_id": ticket_id,
        "rfp_id": rfp_id,
        "status": "analyzing",
        "raw_pdf_path": raw_pdf_path,
        "content_hash": content_hash,
        "created_at": now,
        "updated_at": now,
    }
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        statement = pg_insert(Ticket).values(**values)
    else:
        statement = sqlite_insert(Ticket).values(**values)
    statement = statement.on_conflict_do_nothing(index_elements=["content_hash"])
    result = session.execute(statement)
    session.commit()

    if (result.rowcount or 0) > 0:
        created = session.exec(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        ).one()
        return created, True

    existing = session.exec(
        select(Ticket).where(Ticket.content_hash == content_hash)
    ).one()
    return existing, False


def get_ticket(session: Session, ticket_id: str) -> Ticket | None:
    return session.exec(
        select(Ticket).where(Ticket.ticket_id == ticket_id)
    ).first()


def update_ticket_status(
    session: Session, ticket_id: str, new_status: str
) -> Ticket:
    """Single choke-point for all non-create status writes."""
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise ValueError(f"ticket not found: {ticket_id}")

    result = validate_transition(ticket.status, new_status)
    if not result.is_allowed:
        raise ValueError(
            f"illegal status transition '{ticket.status}' -> '{new_status}'"
            + (f": {result.message}" if result.message else "")
        )

    ticket.status = new_status
    ticket.updated_at = datetime.now(UTC)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


