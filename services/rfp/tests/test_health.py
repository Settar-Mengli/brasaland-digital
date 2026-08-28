"""Health probe tests. ``/livez`` has no dependency calls."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app import app


def test_livez_returns_200() -> None:
    client = TestClient(app)
    response = client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_503_when_redis_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import health as health_module

    monkeypatch.setattr(health_module, "check_postgres", lambda: None)
    monkeypatch.setattr(health_module, "check_checkpoint_path", lambda: None)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "redis" in body["reason"]


def test_readyz_returns_503_when_database_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://u:p@127.0.0.1:1/postgres",
    )
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "postgres" in body["reason"]


def test_readyz_returns_503_when_generation_config_required_but_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import health as health_module

    monkeypatch.setattr(health_module, "check_postgres", lambda: None)
    monkeypatch.setattr(health_module, "check_redis", lambda: None)
    monkeypatch.setattr(health_module, "check_checkpoint_path", lambda: None)
    monkeypatch.setenv("RFP_REQUIRE_GENERATION_CONFIG", "1")
    for name in list(os.environ):
        if name.startswith("GEN_"):
            monkeypatch.delenv(name, raising=False)
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "generation" in body["reason"]


def test_readyz_returns_200_when_generation_config_required_and_tier_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import health as health_module

    monkeypatch.setenv("RFP_REQUIRE_GENERATION_CONFIG", "1")
    monkeypatch.setenv("GEN_1_API_KEY", "test-key")
    monkeypatch.setenv("GEN_1_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("GEN_1_MODEL", "test-model")
    monkeypatch.setattr(health_module, "check_postgres", lambda: None)
    monkeypatch.setattr(health_module, "check_redis", lambda: None)
    monkeypatch.setattr(health_module, "check_checkpoint_path", lambda: None)
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
