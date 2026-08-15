"""Rate-limit coverage for metered knowledge/agent query routes."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid, oauth2_scheme


def _auth_overrides() -> None:
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    app.dependency_overrides[oauth2_scheme] = lambda: "test-token"


def test_agent_query_rate_limit_returns_429() -> None:
    limiter = app.state.limiter
    was = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    _auth_overrides()
    try:
        client = TestClient(app)
        with patch(
            "pipelines.support_agent.invoke_support_agent",
            return_value={"run_id": "r", "answer": "ok"},
        ):
            codes = [
                client.post(
                    "/agent/query", json={"question": "Gold tier?"}
                ).status_code
                for _ in range(12)
            ]
        assert 200 in codes
        assert 429 in codes
    finally:
        app.dependency_overrides.clear()
        limiter.enabled = was
        limiter.reset()


def test_knowledge_query_rate_limit_returns_429() -> None:
    limiter = app.state.limiter
    was = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    try:
        client = TestClient(app)
        with patch(
            "pipelines.rag.query", return_value="Gold needs 50+ points."
        ):
            codes = [
                client.post(
                    "/knowledge/query",
                    json={"question": "How many points for Gold?"},
                ).status_code
                for _ in range(22)
            ]
        assert 200 in codes
        assert 429 in codes
    finally:
        app.dependency_overrides.clear()
        limiter.enabled = was
        limiter.reset()
