"""Owner-or-admin ACL for RFP ticket reads and decisions."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

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
from dependencies import TICKET_ACCESS_DENIED
from pipelines.rfp_intake.repository import create_ticket

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
def _db(tmp_path: Path) -> Generator[None, None, None]:
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
    with patch("upload.DATA_RAW", tmp_path / "raw"):
        yield
    app.dependency_overrides.clear()


def _claims(*, user_id: int, is_admin: bool = False) -> dict[str, object]:
    return {"user_id": user_id, "sub": str(user_id), "is_admin": is_admin}


def _client_as(**claim_kwargs: object):
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_verified_claims] = lambda: _claims(**claim_kwargs)
    return TestClient(app)


def test_owner_can_get_own_ticket() -> None:
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-own",
            content_hash="hash-own",
            raw_pdf_path="/tmp/o.pdf",
            owner_user_uuid="7",
        )
        ticket_id = ticket.ticket_id

    client = _client_as(user_id=7)
    response = client.get(f"/rfp/tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json()["ticket_id"] == ticket_id


def test_non_owner_denied_on_get_and_decision() -> None:
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-other",
            content_hash="hash-other",
            raw_pdf_path="/tmp/x.pdf",
            owner_user_uuid="7",
        )
        ticket_id = ticket.ticket_id

    client = _client_as(user_id=99)
    assert client.get(f"/rfp/tickets/{ticket_id}").status_code == 403
    assert (
        client.get(f"/rfp/tickets/{ticket_id}").json()["detail"]
        == TICKET_ACCESS_DENIED
    )
    denied = client.post(
        f"/rfp/tickets/{ticket_id}/ceo/decision",
        json={"action": "approve"},
    )
    assert denied.status_code == 403


def test_admin_can_access_any_ticket() -> None:
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-admin",
            content_hash="hash-admin",
            raw_pdf_path="/tmp/a.pdf",
            owner_user_uuid="7",
        )
        ticket_id = ticket.ticket_id

    client = _client_as(user_id=1, is_admin=True)
    assert client.get(f"/rfp/tickets/{ticket_id}").status_code == 200


def test_legacy_null_owner_denied_for_non_admin() -> None:
    with Session(_test_engine) as session:
        ticket, _ = create_ticket(
            session,
            rfp_id="rfp-legacy",
            content_hash="hash-legacy",
            raw_pdf_path="/tmp/l.pdf",
            owner_user_uuid=None,
        )
        ticket_id = ticket.ticket_id

    client = _client_as(user_id=7)
    response = client.get(f"/rfp/tickets/{ticket_id}")
    assert response.status_code == 403

    admin = _client_as(user_id=1, is_admin=True)
    assert admin.get(f"/rfp/tickets/{ticket_id}").status_code == 200


def test_upload_stamps_owner() -> None:
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_verified_claims] = lambda: _claims(user_id=55)
    client = TestClient(app)
    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    with patch("routers.rfp.process_rfp.delay"):
        response = client.post(
            "/rfp/tickets",
            files={"file": ("doc.pdf", pdf, "application/pdf")},
        )
    assert response.status_code == 202
    ticket_id = response.json()["ticket_id"]
    with Session(_test_engine) as session:
        from pipelines.rfp_intake.repository import get_ticket

        row = get_ticket(session, ticket_id)
        assert row is not None
        assert row.owner_user_uuid == "55"
