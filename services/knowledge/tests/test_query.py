"""API tests for POST /knowledge/query."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from dependencies import get_current_user_uuid


def test_query_unauthorized() -> None:
    client = TestClient(app)
    response = client.post("/knowledge/query", json={"question": "Gold tier?"})
    assert response.status_code == 401


def test_query_success_with_mocked_rag() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_current_user_uuid] = lambda: "42"
    try:
        with patch(
            "pipelines.rag.query", return_value="Gold requires 50+ points."
        ) as query_mock:
            response = client.post(
                "/knowledge/query",
                json={"question": "How many points for Gold?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"answer": "Gold requires 50+ points."}
    query_mock.assert_called_once_with("How many points for Gold?")
