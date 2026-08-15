"""Celery process_rfp_approval tests (graph/LLM mocked)."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite://")

import config  # noqa: F401
import pipelines.rfp_intake.models as rfp_models  # noqa: F401
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_ticket,
    save_department_sections,
    save_rfp_metadata,
    update_department_section,
    update_ticket_status,
)

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    tables = [
        rfp_models.Ticket.__table__,
        rfp_models.RfpMetadata.__table__,
        rfp_models.DepartmentSection.__table__,
        rfp_models.FinalDocument.__table__,
    ]
    SQLModel.metadata.drop_all(_test_engine, tables=tables)
    SQLModel.metadata.create_all(_test_engine, tables=tables)
    with Session(_test_engine) as session:
        yield session


def _seed_under_evaluation(session: Session) -> str:
    ticket, _ = create_ticket(
        session,
        rfp_id="rfp-appr",
        content_hash="hash-appr",
        raw_pdf_path="/tmp/a.pdf",
        owner_user_uuid="42",
    )
    save_rfp_metadata(
        session,
        rfp_id=ticket.rfp_id,
        metadata={
            "client_name": "Acme",
            "departments_needed": ["marketing", "operaciones"],
            "budget_range": "USD 10000 / COP 40000000",
        },
    )
    save_department_sections(
        session,
        ticket_id=ticket.ticket_id,
        sections=[
            {"department_id": "marketing", "key_aspects": ["brand"]},
            {"department_id": "operaciones", "key_aspects": ["ops"]},
        ],
    )
    for dept, draft in (
        ("marketing", "m draft"),
        ("operaciones", "o draft"),
    ):
        update_department_section(
            session,
            ticket_id=ticket.ticket_id,
            department_id=dept,
            draft_content=draft,
            evaluation_results={"overall_pass": True},
        )
    update_ticket_status(session, ticket.ticket_id, "intake_complete")
    update_ticket_status(session, ticket.ticket_id, "drafting")
    update_ticket_status(session, ticket.ticket_id, "under_evaluation")
    return ticket.ticket_id


class _FakeInterrupt:
    def __init__(self, interrupt_id: str) -> None:
        self.id = interrupt_id
        self.value = {"department": "x"}


def test_process_rfp_approval_starts_threads_and_flips(session: Session) -> None:
    ticket_id = _seed_under_evaluation(session)

    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = [
        {"__interrupt__": [_FakeInterrupt("int-mkt")]},
        {"__interrupt__": [_FakeInterrupt("int-ops")]},
    ]
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("tasks.engine", _test_engine),
        patch("tasks.ensure_schema", lambda: None),
        patch(
            "tasks.extract_all_sections",
            return_value={
                "marketing": {"cost": 1.0, "setup_days": 2.0, "price_per_cover": None},
                "operaciones": {
                    "cost": 3.0,
                    "setup_days": 4.0,
                    "price_per_cover": 5.0,
                },
            },
        ),
        patch(
            "tasks.run_arbitration",
            return_value={
                "conflicts": [],
                "ceo_approval_required": False,
                "section_stamps": {},
            },
        ),
        patch("tasks.checkpointer_cm", return_value=fake_cm),
        patch("tasks.build_dept_approval_graph", return_value=fake_graph),
    ):
        from tasks import process_rfp_approval

        result = process_rfp_approval.run(ticket_id)

    assert result["status"] == "waiting_for_approval"
    ticket = get_ticket(session, ticket_id)
    assert ticket is not None
    assert ticket.status == "waiting_for_approval"
    rows = {r.department_id: r for r in get_department_sections(session, ticket_id)}
    assert rows["marketing"].evaluation_results["interrupt_id"] == "int-mkt"
    assert rows["operaciones"].evaluation_results["interrupt_id"] == "int-ops"
    assert rows["marketing"].evaluation_results["cost"] == 1.0
    assert "arbitration" in rows["marketing"].evaluation_results
    assert fake_graph.invoke.call_count == 2


def test_process_rfp_approval_crash_before_flip_stays_under_evaluation(
    session: Session,
) -> None:
    ticket_id = _seed_under_evaluation(session)

    with (
        patch("tasks.engine", _test_engine),
        patch("tasks.ensure_schema", lambda: None),
        patch("tasks.extract_all_sections", side_effect=RuntimeError("boom")),
    ):
        from tasks import process_rfp_approval

        result = process_rfp_approval.run(ticket_id)

    assert result["status"] == "under_evaluation"
    ticket = get_ticket(session, ticket_id)
    assert ticket is not None
    assert ticket.status == "under_evaluation"
    rows = get_department_sections(session, ticket_id)
    assert any(
        (r.evaluation_results or {}).get("needs_human_review") is True for r in rows
    )
