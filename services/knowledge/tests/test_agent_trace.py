"""API tests for GET /agent/trace/{run_id}."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid


def test_agent_trace_unauthorized() -> None:
    client = TestClient(app)
    response = client.get("/agent/trace/some-run-id")
    assert response.status_code == 401


def test_agent_trace_not_found() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    try:
        with patch("pipelines.support_agent.get_trace", return_value=None):
            response = client.get("/agent/trace/unknown-run-id")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "trace not found"}


def test_agent_trace_success() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    fake_trace = {
        "run_id": "run-ok",
        "nodes": [{"node": "validate_question"}],
        "final": {"answer": "ok", "error": None},
    }
    try:
        with patch("pipelines.support_agent.get_trace", return_value=fake_trace):
            response = client.get("/agent/trace/run-ok")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == fake_trace
