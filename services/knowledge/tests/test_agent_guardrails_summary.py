"""API tests for GET /agent/guardrails/summary."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid, oauth2_scheme


def _auth_overrides() -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"


def test_guardrails_summary_unauthorized() -> None:
    client = TestClient(app)
    response = client.get("/agent/guardrails/summary")
    assert response.status_code == 401


def test_guardrails_summary_process_wide() -> None:
    client = TestClient(app)
    _auth_overrides()
    try:
        with patch(
            "pipelines.guardrails.get_guardrail_summary",
            return_value={
                "structural": 1,
                "content": 2,
                "security": 3,
                "sessions": 1,
            },
        ):
            response = client.get("/agent/guardrails/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["security"] == 3


def test_guardrails_summary_session_scoped() -> None:
    client = TestClient(app)
    _auth_overrides()
    try:
        with patch(
            "pipelines.guardrails.get_guardrail_summary",
            return_value={
                "structural": 0,
                "content": 0,
                "security": 2,
                "session_id": "s1",
                "extraction_turns": 2,
            },
        ) as summary_mock:
            response = client.get(
                "/agent/guardrails/summary",
                params={"session_id": "s1"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["extraction_turns"] == 2
    summary_mock.assert_called_once_with("s1")
