"""In-memory SQLite tests for RFP ticket repository (atomic create + status)."""

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
from pipelines.rfp_intake.models import Ticket
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_ticket,
    update_ticket_status,
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


def test_create_ticket_first_time_returns_created(session: Session) -> None:
    rfp_id = str(uuid4())
    ticket, created = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash="hash-a",
        raw_pdf_path="data/raw/seed/a.pdf",
    )

    assert created is True
    assert ticket.status == "analyzing"
    assert ticket.rfp_id == rfp_id
    assert ticket.content_hash == "hash-a"


def test_create_ticket_same_hash_is_idempotent(session: Session) -> None:
    rfp_id = str(uuid4())
    first, created_first = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash="hash-same",
        raw_pdf_path="data/raw/seed/a.pdf",
    )
    second, created_second = create_ticket(
        session,
        rfp_id=str(uuid4()),
        content_hash="hash-same",
        raw_pdf_path="data/raw/seed/b.pdf",
    )

    assert created_first is True
    assert created_second is False
    assert second.ticket_id == first.ticket_id

    rows = session.exec(select(Ticket).where(Ticket.content_hash == "hash-same")).all()
    assert len(rows) == 1


def test_create_ticket_different_hash_creates_distinct(session: Session) -> None:
    a, _ = create_ticket(
        session,
        rfp_id=str(uuid4()),
        content_hash="hash-1",
        raw_pdf_path="data/raw/seed/a.pdf",
    )
    b, created = create_ticket(
        session,
        rfp_id=str(uuid4()),
        content_hash="hash-2",
        raw_pdf_path="data/raw/seed/b.pdf",
    )

    assert created is True
    assert a.ticket_id != b.ticket_id


def test_get_ticket_round_trip(session: Session) -> None:
    ticket, _ = create_ticket(
        session,
        rfp_id=str(uuid4()),
        content_hash="hash-get",
        raw_pdf_path="data/raw/seed/a.pdf",
    )
    loaded = get_ticket(session, ticket.ticket_id)

    assert loaded is not None
    assert loaded.ticket_id == ticket.ticket_id
    assert get_ticket(session, "missing-id") is None


def test_update_ticket_status_legal_and_illegal(session: Session) -> None:
    ticket, _ = create_ticket(
        session,
        rfp_id=str(uuid4()),
        content_hash="hash-status",
        raw_pdf_path="data/raw/seed/a.pdf",
    )

    advanced = update_ticket_status(session, ticket.ticket_id, "intake_complete")
    assert advanced.status == "intake_complete"

    with pytest.raises(ValueError, match="illegal status transition"):
        update_ticket_status(session, ticket.ticket_id, "analyzing")
