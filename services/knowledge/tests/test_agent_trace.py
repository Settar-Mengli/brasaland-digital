"""API tests for GET /agent/trace/{run_id}."""

from __future__ import annotations

from unittest.mock import patch

from brasaland_auth_verify.deps import get_verified_claims
from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid


def _auth_as(*, user_id: str = "42", is_admin: bool = False) -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: user_id
    app.dependency_overrides[get_verified_claims] = lambda: {
        "user_id": int(user_id) if user_id.isdigit() else user_id,
        "sub": user_id,
        "is_admin": is_admin,
    }


def test_agent_trace_unauthorized() -> None:
    client = TestClient(app)
    response = client.get("/agent/trace/some-run-id")
    assert response.status_code == 401


def test_agent_trace_not_found() -> None:
    client = TestClient(app)
    _auth_as(user_id="42")
    try:
        with patch("pipelines.support_agent.get_trace", return_value=None):
            response = client.get("/agent/trace/unknown-run-id")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "trace not found"}


def test_agent_trace_success() -> None:
    client = TestClient(app)
    _auth_as(user_id="42")
    fake_trace = {
        "run_id": "run-ok",
        "owner_user_uuid": "42",
        "nodes": [{"node": "validate_question"}],
        "final": {"answer": "ok", "error": None},
    }
    try:
        with patch(
            "pipelines.support_agent.get_trace", return_value=fake_trace
        ) as get_mock:
            response = client.get("/agent/trace/run-ok")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == fake_trace
    assert get_mock.call_args.kwargs.get("requester_user_uuid") == "42"
    assert get_mock.call_args.kwargs.get("is_admin") is False


def test_agent_trace_cross_user_denied() -> None:
    client = TestClient(app)
    _auth_as(user_id="99")
    try:
        with patch("pipelines.support_agent.get_trace", return_value=None):
            response = client.get("/agent/trace/run-owned-by-other")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
