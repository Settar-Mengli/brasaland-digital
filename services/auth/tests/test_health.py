"""Health probe tests. ``/livez`` has no TinyDB or other dependency calls."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
from auth.db import reset_db


def test_livez_returns_200() -> None:
    with TestClient(app_module.app) as client:
        response = client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_200_when_tinydb_writable() -> None:
    with TestClient(app_module.app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_503_when_tinydb_parent_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("AUTH_DB_PATH", str(blocker / "users.json"))
    reset_db()

    with TestClient(app_module.app) as client:
        response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "tinydb" in body["reason"]
