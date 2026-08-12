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
    save_department_sections,
    save_rfp_metadata,
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
