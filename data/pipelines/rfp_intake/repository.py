"""Atomic ticket create and status updates for RFP intake."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select

from pipelines.rfp_intake.lifecycle import validate_transition
from pipelines.rfp_intake.models import (
    DepartmentSection,
    FinalDocument,
    RfpMetadata,
    Ticket,
)


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


_METADATA_COLUMNS = (
    "client_name",
    "location",
    "service_type",
    "scope",
    "deadline",
    "budget_range",
    "departments_needed",
    "readability_metrics",
    "open_questions",
)


def save_rfp_metadata(
    session: Session,
    *,
    rfp_id: str,
    metadata: dict[str, Any],
) -> RfpMetadata:
    """Upsert rfp_metadata by rfp_id from a metadata dict (graph extract shape)."""
    now = datetime.now(UTC)
    existing = session.get(RfpMetadata, rfp_id)
    if existing is None:
        row = RfpMetadata(rfp_id=rfp_id, created_at=now, updated_at=now)
        for key in _METADATA_COLUMNS:
            if key in metadata:
                setattr(row, key, metadata[key])
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    for key in _METADATA_COLUMNS:
        if key in metadata:
            setattr(existing, key, metadata[key])
    existing.updated_at = now
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def save_department_sections(
    session: Session,
    *,
    ticket_id: str,
    sections: list[dict[str, Any]],
) -> list[DepartmentSection]:
    """Insert department_section rows (approval_status defaults to pending)."""
    rows: list[DepartmentSection] = []
    for section in sections:
        row = DepartmentSection(
            ticket_id=ticket_id,
            department_id=str(section["department_id"]),
            key_aspects=section.get("key_aspects"),
            draft_content=section.get("draft_content"),
            evaluation_results=section.get("evaluation_results"),
        )
        session.add(row)
        rows.append(row)
    session.commit()
    for row in rows:
        session.refresh(row)
    return rows


def get_department_sections(
    session: Session, ticket_id: str
) -> list[DepartmentSection]:
    """Return all department_section rows for a ticket."""
    return list(
        session.exec(
            select(DepartmentSection).where(
                DepartmentSection.ticket_id == ticket_id
            )
        ).all()
    )


def get_rfp_metadata(session: Session, rfp_id: str) -> RfpMetadata | None:
    """Return the rfp_metadata row for ``rfp_id``, or None if missing."""
    return session.get(RfpMetadata, rfp_id)


def update_department_section(
    session: Session,
    *,
    ticket_id: str,
    department_id: str,
    draft_content: str,
    evaluation_results: dict[str, Any],
) -> DepartmentSection:
    """Update draft_content and evaluation_results for one (ticket, department) row.

    Enforces a single matching row in application code (no DB unique on the pair).
    """
    rows = list(
        session.exec(
            select(DepartmentSection).where(
                DepartmentSection.ticket_id == ticket_id,
                DepartmentSection.department_id == department_id,
            )
        ).all()
    )
    if len(rows) == 0:
        raise ValueError(
            f"department_section not found: ticket_id={ticket_id!r} "
            f"department_id={department_id!r}"
        )
    if len(rows) > 1:
        raise ValueError(
            f"multiple department_section rows for ticket_id={ticket_id!r} "
            f"department_id={department_id!r} (count={len(rows)})"
        )

    row = rows[0]
    row.draft_content = draft_content
    row.evaluation_results = evaluation_results
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _department_section_row(
    session: Session, *, ticket_id: str, department_id: str
) -> DepartmentSection:
    """Load exactly one department_section for (ticket_id, department_id)."""
    rows = list(
        session.exec(
            select(DepartmentSection).where(
                DepartmentSection.ticket_id == ticket_id,
                DepartmentSection.department_id == department_id,
            )
        ).all()
    )
    if len(rows) == 0:
        raise ValueError(
            f"department_section not found: ticket_id={ticket_id!r} "
            f"department_id={department_id!r}"
        )
    if len(rows) > 1:
        raise ValueError(
            f"multiple department_section rows for ticket_id={ticket_id!r} "
            f"department_id={department_id!r} (count={len(rows)})"
        )
    return rows[0]


def save_final_document(
    session: Session,
    *,
    ticket_id: str,
    sections: list[Any],
    total_estimated_value: str | None,
) -> FinalDocument:
    """Upsert the single FinalDocument for a ticket (§2.2: one per ticket).

    If a row exists for ``ticket_id``, update sections, total_estimated_value, and
    refresh ``generated_at``. Otherwise insert.
    """
    now = datetime.now(UTC)
    existing = session.exec(
        select(FinalDocument).where(FinalDocument.ticket_id == ticket_id)
    ).first()
    if existing is None:
        row = FinalDocument(
            ticket_id=ticket_id,
            sections=sections,
            total_estimated_value=total_estimated_value,
            generated_at=now,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    existing.sections = sections
    existing.total_estimated_value = total_estimated_value
    existing.generated_at = now
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def update_department_section_approval(
    session: Session,
    *,
    ticket_id: str,
    department_id: str,
    approval_status: str,
    approver: str | None,
    approved_at: datetime | None,
) -> DepartmentSection:
    """Update approval_status, approver, and approved_at only (not draft/eval)."""
    row = _department_section_row(
        session, ticket_id=ticket_id, department_id=department_id
    )
    row.approval_status = approval_status
    row.approver = approver
    row.approved_at = approved_at
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def merge_evaluation_results(
    session: Session,
    *,
    ticket_id: str,
    department_id: str,
    patch: dict[str, Any],
) -> DepartmentSection:
    """Shallow-merge ``patch`` into evaluation_results without wiping P2 keys.

    P2 replaces the whole dict via ``update_department_section``; P3 must use this
    path to add keys such as cost / setup_days / interrupt_id.
    """
    row = _department_section_row(
        session, ticket_id=ticket_id, department_id=department_id
    )
    existing = dict(row.evaluation_results or {})
    existing.update(patch)
    row.evaluation_results = existing
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


