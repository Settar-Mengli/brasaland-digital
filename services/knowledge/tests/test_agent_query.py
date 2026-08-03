"""API tests for POST /agent/query."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid, oauth2_scheme


def _auth_overrides() -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"


def test_agent_query_unauthorized() -> None:
    client = TestClient(app)
    response = client.post("/agent/query", json={"question": "Gold tier?"})
    assert response.status_code == 401


def test_agent_query_success() -> None:
    client = TestClient(app)
    _auth_overrides()
    try:
        with patch(
            "pipelines.support_agent.invoke_support_agent",
            return_value={"run_id": "run-1", "answer": "Gold needs 50+ points."},
        ) as invoke_mock:
            response = client.post(
                "/agent/query",
                json={"question": "How many points for Gold?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "run-1",
        "answer": "Gold needs 50+ points.",
    }
    invoke_mock.assert_called_once_with(
        "How many points for Gold?",
        access_token="test-token",
        user_id="42",
    )


def test_agent_query_empty_returns_detail() -> None:
    client = TestClient(app)
    _auth_overrides()
    try:
        with patch(
            "pipelines.support_agent.invoke_support_agent",
            return_value={"run_id": "run-empty", "error": "question must not be empty"},
        ):
            response = client.post("/agent/query", json={"question": "   "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "question must not be empty"}


def test_agent_query_node_failure_returns_detail() -> None:
    client = TestClient(app)
    _auth_overrides()
    try:
        with patch(
            "pipelines.support_agent.invoke_support_agent",
            return_value={"run_id": "run-fail", "error": "LLM_GATEWAY_API_KEY is not set"},
        ):
            response = client.post(
                "/agent/query",
                json={"question": "Gold tier?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    body = response.json()
    assert body == {"detail": "LLM_GATEWAY_API_KEY is not set"}
    assert "Traceback" not in str(body)
