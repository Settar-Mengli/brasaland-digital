"""API tests for RFP upload + ticket poll (auth override, SQLite, Celery patched)."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import config  # noqa: F401
import pipelines.rfp_intake.models as rfp_models  # noqa: F401
from app import app
from database import get_db
from dependencies import get_current_user_uuid

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
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"

    with patch("upload.DATA_RAW", tmp_path / "raw"):
        yield

    app.dependency_overrides.clear()


@pytest.fixture()
def client(_db_and_auth: None):
    from fastapi.testclient import TestClient

    return TestClient(app)


def _tiny_pdf() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def test_post_tickets_unauthorized() -> None:
    from fastapi.testclient import TestClient

    app.dependency_overrides.clear()
    bare = TestClient(app)
    response = bare.post(
        "/rfp/tickets",
        files={"file": ("x.pdf", _tiny_pdf(), "application/pdf")},
    )
    assert response.status_code == 401


def test_get_ticket_unauthorized() -> None:
    from fastapi.testclient import TestClient

    app.dependency_overrides.clear()
    bare = TestClient(app)
    response = bare.get("/rfp/tickets/does-not-exist")
    assert response.status_code == 401


def test_upload_valid_pdf_returns_202(client) -> None:
    delay = MagicMock()
    with patch("routers.rfp.process_rfp.delay", delay):
        response = client.post(
            "/rfp/tickets",
            files={"file": ("doc.pdf", _tiny_pdf(), "application/pdf")},
        )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "analyzing"
    assert body["ticket_id"]
    assert body["rfp_id"]
    delay.assert_called_once_with(body["ticket_id"])


def test_upload_non_pdf_returns_400(client) -> None:
    response = client.post(
        "/rfp/tickets",
        files={"file": ("x.bin", b"not-a-pdf", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not a valid PDF" in response.json()["detail"]


def test_upload_over_cap_returns_413(client) -> None:
    # Cap check runs during chunked read; magic check is after — start with %PDF-
    # then pad past the limit.
    from upload import MAX_UPLOAD_BYTES

    huge = b"%PDF-" + (b"x" * MAX_UPLOAD_BYTES)
    response = client.post(
        "/rfp/tickets",
        files={"file": ("big.pdf", huge, "application/pdf")},
    )
    assert response.status_code == 413


def test_get_ticket_round_trip_and_404(client) -> None:
    with patch("routers.rfp.process_rfp.delay", MagicMock()):
        created = client.post(
            "/rfp/tickets",
            files={"file": ("doc.pdf", _tiny_pdf(), "application/pdf")},
        )
    ticket_id = created.json()["ticket_id"]
    got = client.get(f"/rfp/tickets/{ticket_id}")
    assert got.status_code == 200
    assert got.json()["ticket_id"] == ticket_id
    assert got.json()["status"] == "analyzing"

    missing = client.get("/rfp/tickets/missing-id")
    assert missing.status_code == 404


def test_duplicate_upload_is_idempotent_and_enqueues_once(client) -> None:
    delay = MagicMock()
    payload = _tiny_pdf()
    with patch("routers.rfp.process_rfp.delay", delay):
        first = client.post(
            "/rfp/tickets",
            files={"file": ("a.pdf", payload, "application/pdf")},
        )
        second = client.post(
            "/rfp/tickets",
            files={"file": ("b.pdf", payload, "application/pdf")},
        )
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["ticket_id"] == second.json()["ticket_id"]
    assert delay.call_count == 1


def test_post_response_unauthorized() -> None:
    from fastapi.testclient import TestClient

    app.dependency_overrides.clear()
    bare = TestClient(app)
    response = bare.post("/rfp/tickets/some-id/response")
    assert response.status_code == 401


def test_post_response_409_when_not_intake_complete(client) -> None:
    with patch("routers.rfp.process_rfp.delay", MagicMock()):
        created = client.post(
            "/rfp/tickets",
            files={"file": ("doc.pdf", _tiny_pdf(), "application/pdf")},
        )
    ticket_id = created.json()["ticket_id"]
    # Upload leaves status at analyzing — response must 409.
    delay = MagicMock()
    with patch("routers.rfp.process_rfp_response.delay", delay):
        response = client.post(f"/rfp/tickets/{ticket_id}/response")
    assert response.status_code == 409
    delay.assert_not_called()


def test_post_response_202_when_intake_complete(client) -> None:
    from pipelines.rfp_intake.repository import (
        create_ticket,
        save_rfp_metadata,
        update_ticket_status,
    )

    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-response-ok",
            content_hash="hash-response-ok",
            raw_pdf_path="/tmp/ok.pdf",
        )
        save_rfp_metadata(
            session,
            rfp_id=ticket.rfp_id,
            metadata={"client_name": "Acme", "departments_needed": ["marketing"]},
        )
        update_ticket_status(session, ticket.ticket_id, "intake_complete")
        ticket_id = ticket.ticket_id

    delay = MagicMock()
    with patch("routers.rfp.process_rfp_response.delay", delay):
        response = client.post(f"/rfp/tickets/{ticket_id}/response")
    assert response.status_code == 202
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["status"] == "intake_complete"
    delay.assert_called_once_with(ticket_id)


def test_get_ticket_includes_sections(client) -> None:
    from pipelines.rfp_intake.repository import (
        create_ticket,
        save_department_sections,
        update_department_section,
    )

    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-sections",
            content_hash="hash-sections",
            raw_pdf_path="/tmp/s.pdf",
        )
        save_department_sections(
            session,
            ticket_id=ticket.ticket_id,
            sections=[{"department_id": "marketing", "key_aspects": ["brand"]}],
        )
        update_department_section(
            session,
            ticket_id=ticket.ticket_id,
            department_id="marketing",
            draft_content="Draft text",
            evaluation_results={"overall_pass": True, "iterations": 1},
        )
        ticket_id = ticket.ticket_id

    got = client.get(f"/rfp/tickets/{ticket_id}")
    assert got.status_code == 200
    body = got.json()
    assert "sections" in body
    assert isinstance(body["sections"], list)
    assert len(body["sections"]) == 1
    section = body["sections"][0]
    assert section["department_id"] == "marketing"
    assert section["key_aspects"] == ["brand"]
    assert section["draft_content"] == "Draft text"
    assert section["evaluation_results"]["overall_pass"] is True
    assert section["approval_status"] == "pending"
