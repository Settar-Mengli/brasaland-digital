"""In-memory SQLite tests for RFP metadata / department section writers."""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake import models as rfp_models  # noqa: F401
from pipelines.rfp_intake.models import DepartmentSection, RfpMetadata
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_rfp_metadata,
    save_department_sections,
    save_rfp_metadata,
    update_department_section,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(
        engine,
        tables=[
            rfp_models.Ticket.__table__,
            rfp_models.RfpMetadata.__table__,
            rfp_models.DepartmentSection.__table__,
            rfp_models.FinalDocument.__table__,
        ],
    )
    with Session(engine) as sess:
        yield sess


def test_save_rfp_metadata_insert_then_update(session: Session) -> None:
    rfp_id = str(uuid4())
    row = save_rfp_metadata(
        session,
        rfp_id=rfp_id,
        metadata={
            "client_name": "Sunset Bay",
            "location": "Florida",
            "scope": "concession",
            "open_questions": ["covers/day?"],
        },
    )
    assert row.rfp_id == rfp_id
    assert row.client_name == "Sunset Bay"
    assert row.open_questions == ["covers/day?"]

    updated = save_rfp_metadata(
        session,
        rfp_id=rfp_id,
        metadata={
            "client_name": "Sunset Bay Resorts",
            "deadline": "2026-04-15",
            "departments_needed": ["marketing", "operaciones"],
            "readability_metrics": {"flesch_reading_ease": 55.0},
        },
    )
    assert updated.rfp_id == rfp_id
    assert updated.client_name == "Sunset Bay Resorts"
    assert updated.deadline == "2026-04-15"
    assert updated.location == "Florida"  # untouched when absent from patch
    assert updated.departments_needed == ["marketing", "operaciones"]
    assert session.exec(select(RfpMetadata)).all().__len__() == 1


def test_save_department_sections_pending(session: Session) -> None:
    rfp_id = str(uuid4())
    ticket, _ = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=f"hash-{rfp_id}",
        raw_pdf_path="/tmp/x.pdf",
    )
    rows = save_department_sections(
        session,
        ticket_id=ticket.ticket_id,
        sections=[
            {"department_id": "marketing", "key_aspects": ["brand"]},
            {"department_id": "operaciones", "key_aspects": ["staffing"]},
        ],
    )
    assert len(rows) == 2
    assert all(r.approval_status == "pending" for r in rows)
    stored = session.exec(
        select(DepartmentSection).where(
            DepartmentSection.ticket_id == ticket.ticket_id
        )
    ).all()
    assert len(stored) == 2


def test_get_department_sections_filters_by_ticket(session: Session) -> None:
    rfp_a = str(uuid4())
    rfp_b = str(uuid4())
    ticket_a, _ = create_ticket(
        session,
        rfp_id=rfp_a,
        content_hash=f"hash-{rfp_a}",
        raw_pdf_path="/tmp/a.pdf",
    )
    ticket_b, _ = create_ticket(
        session,
        rfp_id=rfp_b,
        content_hash=f"hash-{rfp_b}",
        raw_pdf_path="/tmp/b.pdf",
    )
    save_department_sections(
        session,
        ticket_id=ticket_a.ticket_id,
        sections=[
            {"department_id": "marketing", "key_aspects": ["brand"]},
            {"department_id": "operaciones", "key_aspects": ["staffing"]},
        ],
    )
    save_department_sections(
        session,
        ticket_id=ticket_b.ticket_id,
        sections=[{"department_id": "procurement", "key_aspects": ["cost"]}],
    )

    rows = get_department_sections(session, ticket_a.ticket_id)
    assert len(rows) == 2
    assert {r.department_id for r in rows} == {"marketing", "operaciones"}
    assert all(r.ticket_id == ticket_a.ticket_id for r in rows)


def test_get_rfp_metadata_found_and_missing(session: Session) -> None:
    rfp_id = str(uuid4())
    save_rfp_metadata(
        session,
        rfp_id=rfp_id,
        metadata={
            "client_name": "Andes Tech",
            "departments_needed": ["marketing", "operaciones", "procurement"],
        },
    )
    found = get_rfp_metadata(session, rfp_id)
    assert found is not None
    assert found.client_name == "Andes Tech"
    assert found.departments_needed == [
        "marketing",
        "operaciones",
        "procurement",
    ]
    assert get_rfp_metadata(session, "missing-rfp-id") is None


def test_update_department_section_happy_path(session: Session) -> None:
    rfp_id = str(uuid4())
    ticket, _ = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=f"hash-{rfp_id}",
        raw_pdf_path="/tmp/x.pdf",
    )
    save_department_sections(
        session,
        ticket_id=ticket.ticket_id,
        sections=[{"department_id": "marketing", "key_aspects": ["brand"]}],
    )
    evaluation = {
        "overall_pass": True,
        "iterations": 1,
        "exhausted": False,
        "needs_human_review": False,
    }
    updated = update_department_section(
        session,
        ticket_id=ticket.ticket_id,
        department_id="marketing",
        draft_content="Proposal draft for marketing.",
        evaluation_results=evaluation,
    )
    assert updated.draft_content == "Proposal draft for marketing."
    assert updated.evaluation_results == evaluation

    reloaded = session.exec(
        select(DepartmentSection).where(
            DepartmentSection.ticket_id == ticket.ticket_id,
            DepartmentSection.department_id == "marketing",
        )
    ).one()
    assert reloaded.draft_content == "Proposal draft for marketing."
    assert reloaded.evaluation_results == evaluation
    assert reloaded.key_aspects == ["brand"]


def test_update_department_section_raises_when_missing(session: Session) -> None:
    rfp_id = str(uuid4())
    ticket, _ = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=f"hash-{rfp_id}",
        raw_pdf_path="/tmp/x.pdf",
    )
    with pytest.raises(ValueError, match="department_section not found"):
        update_department_section(
            session,
            ticket_id=ticket.ticket_id,
            department_id="marketing",
            draft_content="x",
            evaluation_results={},
        )


def test_update_department_section_raises_when_duplicate(session: Session) -> None:
    rfp_id = str(uuid4())
    ticket, _ = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=f"hash-{rfp_id}",
        raw_pdf_path="/tmp/x.pdf",
    )
    # Two rows with the same (ticket_id, department_id) — allowed without a unique.
    save_department_sections(
        session,
        ticket_id=ticket.ticket_id,
        sections=[
            {"department_id": "marketing", "key_aspects": ["a"]},
            {"department_id": "marketing", "key_aspects": ["b"]},
        ],
    )
    with pytest.raises(ValueError, match="multiple department_section rows"):
        update_department_section(
            session,
            ticket_id=ticket.ticket_id,
            department_id="marketing",
            draft_content="x",
            evaluation_results={},
        )
