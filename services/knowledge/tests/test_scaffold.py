"""Scaffold smoke tests for the knowledge service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


def test_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "knowledge"}
