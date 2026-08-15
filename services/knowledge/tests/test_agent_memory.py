"""API tests for GET /agent/memory and /agent/memory/audit."""

from __future__ import annotations

from unittest.mock import patch

from brasaland_auth_verify.deps import get_verified_claims, require_admin
from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid, oauth2_scheme


def _auth_as(*, user_id: str = "42", is_admin: bool = False) -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: user_id
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"
    app.dependency_overrides[get_verified_claims] = lambda: {
        "user_id": int(user_id) if user_id.isdigit() else user_id,
        "sub": user_id,
        "is_admin": is_admin,
    }
    if is_admin:
        app.dependency_overrides[require_admin] = lambda: user_id
    else:
        app.dependency_overrides.pop(require_admin, None)


def test_agent_memory_unauthorized() -> None:
    client = TestClient(app)
    assert client.get("/agent/memory").status_code == 401
    assert client.get("/agent/memory/audit").status_code == 401


def test_agent_memory_and_audit_admin() -> None:
    client = TestClient(app)
    _auth_as(user_id="42", is_admin=True)
    try:
        with (
            patch(
                "pipelines.memory_store.read_memory",
                return_value=[
                    {
                        "location": "medellin",
                        "category": "suppliers",
                        "summary": "Delivers Wednesdays",
                        "updated_at": "t",
                        "proposal_id": "p1",
                    }
                ],
            ) as read_mock,
            patch(
                "pipelines.memory_store.list_audit",
                return_value=[
                    {
                        "id": "a1",
                        "outcome": "proposed",
                        "originating_message": "x",
                    }
                ],
            ),
        ):
            mem = client.get("/agent/memory", params={"location": "medellin"})
            audit = client.get("/agent/memory/audit")
    finally:
        app.dependency_overrides.clear()

    assert mem.status_code == 200
    assert mem.json()["entries"][0]["location"] == "medellin"
    read_mock.assert_called_once()
    assert read_mock.call_args.kwargs.get("user_id") == "42"
    assert audit.status_code == 200
    assert audit.json()["events"][0]["outcome"] == "proposed"


def test_agent_memory_audit_forbidden_for_non_admin() -> None:
    client = TestClient(app)
    _auth_as(user_id="42", is_admin=False)
    try:
        app.dependency_overrides.pop(require_admin, None)
        response = client.get("/agent/memory/audit")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_agent_memory_scoped_to_caller() -> None:
    """Caller identity is forwarded into read_memory (cross-user isolation)."""
    client = TestClient(app)
    _auth_as(user_id="77", is_admin=False)
    try:
        with patch(
            "pipelines.memory_store.read_memory", return_value=[]
        ) as read_mock:
            response = client.get("/agent/memory")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert read_mock.call_args.kwargs.get("user_id") == "77"
