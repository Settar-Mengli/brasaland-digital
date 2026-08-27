"""FastAPI approval decision + GET enrichment tests (graph mocked)."""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite://")

import config  # noqa: F401
import pipelines.rfp_intake.models as rfp_models  # noqa: F401
from brasaland_auth_verify.deps import get_verified_claims
from app import app
from database import get_db
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_ticket,
    merge_evaluation_results,
    save_department_sections,
    save_final_document,
    save_rfp_metadata,
    update_department_section,
    update_department_section_approval,
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


@pytest.fixture(autouse=True)
def _db_and_auth(tmp_path: Path) -> Generator[None, None, None]:
    tables = [
        rfp_models.Ticket.__table__,
        rfp_models.RfpMetadata.__table__,
        rfp_models.DepartmentSection.__table__,
        rfp_models.FinalDocument.__table__,
    ]
    SQLModel.metadata.drop_all(_test_engine, tables=tables)
    SQLModel.metadata.create_all(_test_engine, tables=tables)

    def override_get_db() -> Generator[Session, None, None]:
        with Session(_test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_verified_claims] = lambda: {
        "user_id": 42,
        "sub": "42",
        "is_admin": False,
    }

    with patch("upload.DATA_RAW", tmp_path / "raw"):
        yield

    app.dependency_overrides.clear()


@pytest.fixture()
def client(_db_and_auth: None):
    from fastapi.testclient import TestClient

    return TestClient(app)


def _seed_waiting(
    *,
    departments: list[str] | None = None,
    ceo_required: bool = False,
    key_aspects_by_dept: dict[str, list[str]] | None = None,
) -> str:
    departments = departments or ["marketing"]
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-dec",
            content_hash="hash-dec",
            raw_pdf_path="/tmp/d.pdf",
            owner_user_uuid="42",
        )
        save_rfp_metadata(
            session,
            rfp_id=ticket.rfp_id,
            metadata={
                "client_name": "Acme",
                "departments_needed": departments,
                "budget_range": "USD 60000 / COP 240000000",
            },
        )
        save_department_sections(
            session,
            ticket_id=ticket.ticket_id,
            sections=[
                {
                    "department_id": d,
                    "key_aspects": (key_aspects_by_dept or {}).get(d, [d]),
                }
                for d in departments
            ],
        )
        arb = {
            "conflicts": [],
            "ceo_approval_required": ceo_required,
        }
        for dept in departments:
            update_department_section(
                session,
                ticket_id=ticket.ticket_id,
                department_id=dept,
                draft_content=f"{dept} draft",
                evaluation_results={
                    "overall_pass": True,
                    "cost": 10.0,
                    "interrupt_id": f"int-{dept}",
                    "arbitration": arb,
                },
            )
        update_ticket_status(session, ticket.ticket_id, "intake_complete")
        update_ticket_status(session, ticket.ticket_id, "drafting")
        update_ticket_status(session, ticket.ticket_id, "under_evaluation")
        update_ticket_status(session, ticket.ticket_id, "waiting_for_approval")
        return ticket.ticket_id


_FAIL_REGEN_DRAFT = (
    "We propose catering with pricing in COP and USD. "
    "Setup takes twelve business days. "
    "This offer is valid for 30 days from issuance."
)

_PASS_REGEN_DRAFT = (
    "Brasaland delivers consistent quality, a warm experience, and speed of service. "
    "Our catering proposal covers brand exclusivity for the client. "
    "Pricing is quoted in both COP and USD. "
    "Setup requires 12 business days. "
    "This offer is valid for 30 days from issuance."
)


class _FakeInterrupt:
    def __init__(self, interrupt_id: str, value: dict | None = None) -> None:
        self.id = interrupt_id
        self.value = value or {}


def test_post_approval_202(client) -> None:
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-appr-http",
            content_hash="hash-appr-http",
            raw_pdf_path="/tmp/a.pdf",
            owner_user_uuid="42",
        )
        save_rfp_metadata(
            session,
            rfp_id=ticket.rfp_id,
            metadata={"client_name": "Acme", "departments_needed": ["marketing"]},
        )
        update_ticket_status(session, ticket.ticket_id, "intake_complete")
        update_ticket_status(session, ticket.ticket_id, "drafting")
        update_ticket_status(session, ticket.ticket_id, "under_evaluation")
        ticket_id = ticket.ticket_id

    delay = MagicMock()
    with patch("routers.rfp.process_rfp_approval.delay", delay):
        response = client.post(f"/rfp/tickets/{ticket_id}/approval")
    assert response.status_code == 202
    delay.assert_called_once_with(ticket_id)


def test_decision_approve_finalizes_without_ceo(client) -> None:
    ticket_id = _seed_waiting(departments=["marketing"], ceo_required=False)

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "outcome": "approved",
        "section": {"draft_content": "marketing draft", "cost": 10.0},
    }
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("approval_driver.checkpointer_cm", return_value=fake_cm),
        patch("approval_driver.build_dept_approval_graph", return_value=fake_graph),
        patch(
            "approval_driver.synthesize_final_document",
            return_value={
                "sections": [
                    {
                        "department_id": "marketing",
                        "draft_content": "marketing draft",
                    }
                ],
                "total_estimated_value": "USD 60000 / COP 240000000",
            },
        ),
    ):
        response = client.post(
            f"/rfp/tickets/{ticket_id}/sections/marketing/decision",
            json={"action": "approve"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "approved"
    assert body["status"] == "done"
    assert body["ceo_pending"] is False
    assert fake_graph.invoke.call_args[0][0].resume == {"int-marketing": "approve"}

    with Session(_test_engine) as session:
        ticket = get_ticket(session, ticket_id)
        assert ticket is not None
        assert ticket.status == "done"
        row = get_department_sections(session, ticket_id)[0]
        assert row.approval_status == "approved"
        assert row.approver == "Camila Ospina"


def test_decision_reject_regen_failing_draft_overwrites_stale_pass(client) -> None:
    """C1: real evaluate_all on FAIL draft must clear stale overall_pass=True."""
    ticket_id = _seed_waiting(
        departments=["marketing"],
        ceo_required=False,
        key_aspects_by_dept={"marketing": ["brand exclusivity"]},
    )

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "__interrupt__": [_FakeInterrupt("int-marketing-2", {"draft": "v2"})],
        "section": {
            "draft_content": _FAIL_REGEN_DRAFT,
            "cost": 11.0,
            "setup_days": 3.0,
            "price_per_cover": None,
            "human_feedback": "tighten brand",
        },
        "rework_count": 1,
    }
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("approval_driver.checkpointer_cm", return_value=fake_cm),
        patch("approval_driver.build_dept_approval_graph", return_value=fake_graph),
    ):
        response = client.post(
            f"/rfp/tickets/{ticket_id}/sections/marketing/decision",
            json={"action": "reject", "feedback": "tighten brand"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "pending_reapproval"
    assert body["status"] == "waiting_for_approval"
    resume_map = fake_graph.invoke.call_args[0][0].resume
    assert resume_map == {
        "int-marketing": {"action": "reject", "feedback": "tighten brand"}
    }

    with Session(_test_engine) as session:
        row = get_department_sections(session, ticket_id)[0]
        assert row.draft_content == _FAIL_REGEN_DRAFT
        eval_results = row.evaluation_results or {}
        assert eval_results["interrupt_id"] == "int-marketing-2"
        assert eval_results["cost"] == 11.0
        assert eval_results["overall_pass"] is False
        assert "brand_pillars" in (eval_results.get("compliance") or {}).get(
            "rule_ids", []
        )
        assert eval_results["arbitration"]["ceo_approval_required"] is False
        assert eval_results["human_feedback"] == "tighten brand"
        ticket = get_ticket(session, ticket_id)
        assert ticket is not None
        assert ticket.status == "waiting_for_approval"


def test_decision_reject_regen_passing_draft_writes_fresh_pass(client) -> None:
    """C1: real evaluate_all on PASS draft yields overall_pass True from new text."""
    ticket_id = _seed_waiting(
        departments=["marketing"],
        ceo_required=False,
        key_aspects_by_dept={"marketing": ["brand exclusivity"]},
    )

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "__interrupt__": [_FakeInterrupt("int-marketing-2", {"draft": "v2"})],
        "section": {
            "draft_content": _PASS_REGEN_DRAFT,
            "cost": 11.0,
            "setup_days": 3.0,
            "price_per_cover": None,
            "human_feedback": "looks good after polish",
        },
        "rework_count": 1,
    }
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("approval_driver.checkpointer_cm", return_value=fake_cm),
        patch("approval_driver.build_dept_approval_graph", return_value=fake_graph),
    ):
        response = client.post(
            f"/rfp/tickets/{ticket_id}/sections/marketing/decision",
            json={"action": "reject", "feedback": "looks good after polish"},
        )

    assert response.status_code == 200
    assert response.json()["outcome"] == "pending_reapproval"

    with Session(_test_engine) as session:
        row = get_department_sections(session, ticket_id)[0]
        assert row.draft_content == _PASS_REGEN_DRAFT
        eval_results = row.evaluation_results or {}
        assert eval_results["interrupt_id"] == "int-marketing-2"
        assert eval_results["overall_pass"] is True
        assert (eval_results.get("compliance") or {}).get("pass") is True
        assert (eval_results.get("readability") or {}).get("pass") is True
        assert (eval_results.get("relevance") or {}).get("pass") is True
        assert eval_results["arbitration"]["ceo_approval_required"] is False
        assert eval_results["human_feedback"] == "looks good after polish"


def test_decision_approve_starts_ceo_when_required(client) -> None:
    ticket_id = _seed_waiting(departments=["marketing"], ceo_required=True)

    dept_graph = MagicMock()
    dept_graph.invoke.return_value = {
        "outcome": "approved",
        "section": {"draft_content": "marketing draft"},
    }
    ceo_graph = MagicMock()
    ceo_graph.invoke.return_value = {
        "__interrupt__": [_FakeInterrupt("ceo-int-1")],
    }
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("approval_driver.checkpointer_cm", return_value=fake_cm),
        patch("approval_driver.build_dept_approval_graph", return_value=dept_graph),
        patch("approval_driver.build_ceo_interrupt_graph", return_value=ceo_graph),
    ):
        response = client.post(
            f"/rfp/tickets/{ticket_id}/sections/marketing/decision",
            json={"action": "approve"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "approved"
    assert body["ceo_pending"] is True
    assert body["status"] == "waiting_for_approval"

    with Session(_test_engine) as session:
        ticket = get_ticket(session, ticket_id)
        assert ticket is not None
        assert ticket.status == "waiting_for_approval"
        row = get_department_sections(session, ticket_id)[0]
        assert row.evaluation_results["arbitration"]["ceo_interrupt_id"] == "ceo-int-1"


def test_ceo_approve_goes_done(client) -> None:
    ticket_id = _seed_waiting(departments=["marketing"], ceo_required=True)
    with Session(_test_engine) as session:
        update_department_section_approval(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            approval_status="approved",
            approver="Camila Ospina",
            approved_at=datetime.now(UTC),
        )
        merge_evaluation_results(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            patch={
                "arbitration": {
                    "conflicts": [],
                    "ceo_approval_required": True,
                    "ceo_interrupt_id": "ceo-int-1",
                }
            },
        )

    ceo_graph = MagicMock()
    ceo_graph.invoke.return_value = {
        "ceo_decision": "approved",
        "ceo_approved_at": "2026-01-01T00:00:00+00:00",
    }
    fake_cm = MagicMock()
    fake_cm.__enter__.return_value = MagicMock()
    fake_cm.__exit__.return_value = None

    with (
        patch("approval_driver.checkpointer_cm", return_value=fake_cm),
        patch("approval_driver.build_ceo_interrupt_graph", return_value=ceo_graph),
        patch(
            "approval_driver.synthesize_final_document",
            return_value={
                "sections": [
                    {
                        "department_id": "marketing",
                        "draft_content": "marketing draft",
                    }
                ],
                "total_estimated_value": "USD 60000 / COP 240000000",
            },
        ),
    ):
        response = client.post(
            f"/rfp/tickets/{ticket_id}/ceo/decision",
            json={"action": "approve"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ceo_decision"] == "approved"
    assert body["status"] == "done"
    assert body["final_document"] is not None

    with Session(_test_engine) as session:
        ticket = get_ticket(session, ticket_id)
        assert ticket is not None
        assert ticket.status == "done"


def test_get_enrichment_fields(client) -> None:
    ticket_id = _seed_waiting(departments=["marketing"], ceo_required=True)
    with Session(_test_engine) as session:
        update_department_section_approval(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            approval_status="approved",
            approver="Camila Ospina",
            approved_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        save_final_document(
            session,
            ticket_id=ticket_id,
            sections=[{"department_id": "marketing", "draft_content": "final"}],
            total_estimated_value="USD 1 / COP 1",
            document={
                "header": {
                    "client_name": "Acme",
                    "location": "Bogotá",
                    "service_type": "catering",
                    "generated_at": "2026-01-02T00:00:00+00:00",
                    "ticket_id": ticket_id,
                },
                "sections": [
                    {"department_id": "marketing", "draft_content": "final"}
                ],
                "arbitration_outcomes": {
                    "triggers_fired": [],
                    "resolutions": [],
                },
                "ceo_line": "CEO approval: Mariana Restrepo, 2026-01-02T00:00:00+00:00",
                "total_estimated_value": "USD 1 / COP 1",
                "open_questions": [],
            },
        )
        update_ticket_status(session, ticket_id, "done")

    got = client.get(f"/rfp/tickets/{ticket_id}")
    assert got.status_code == 200
    body = got.json()
    section = body["sections"][0]
    assert section["approver"] == "Camila Ospina"
    assert section["approved_at"] is not None
    assert section["awaiting_decision"] is False
    assert body["arbitration"]["ceo_approval_required"] is True
    assert body["final_document"]["total_estimated_value"] == "USD 1 / COP 1"
    assert body["final_document"]["sections"][0]["draft_content"] == "final"
    assert body["final_document"]["header"]["client_name"] == "Acme"
    assert body["final_document"]["ceo_line"].startswith("CEO approval:")
    assert "arbitration_outcomes" in body["final_document"]
