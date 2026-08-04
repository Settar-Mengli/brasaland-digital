"""API tests for GET /agent/memory and /agent/memory/audit."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid, oauth2_scheme


def _auth_overrides() -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"


def test_agent_memory_unauthorized() -> None:
    client = TestClient(app)
    assert client.get("/agent/memory").status_code == 401
    assert client.get("/agent/memory/audit").status_code == 401


def test_agent_memory_and_audit() -> None:
    client = TestClient(app)
    _auth_overrides()
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
            ),
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
    assert audit.status_code == 200
    assert audit.json()["events"][0]["outcome"] == "proposed"
