"""Auth rate-limit coverage (login)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app
from brasaland_proxy_trust.rate_limit_key import clear_trusted_proxy_cache
from tests.helpers import login_form


@pytest.fixture(autouse=True)
def _reset_proxy_trust(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    clear_trusted_proxy_cache()


def test_login_rate_limit_returns_429() -> None:
    limiter = app.state.limiter
    was = limiter.enabled
    limiter.enabled = True
    try:
        client = TestClient(app)
        codes: list[int] = []
        for _ in range(8):
            response = client.post(
                "/auth/login",
                data=login_form("nobody@brasaland.com", "wrong-password"),
            )
            codes.append(response.status_code)
        assert 429 in codes
        assert codes.count(401) >= 1
    finally:
        limiter.enabled = was


def test_login_rate_limit_buckets_differ_by_forwarded_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_IPS", "testclient")
    clear_trusted_proxy_cache()
    limiter = app.state.limiter
    was = limiter.enabled
    limiter.enabled = True
    try:
        client = TestClient(app)
        for _ in range(6):
            response = client.post(
                "/auth/login",
                data=login_form("nobody@brasaland.com", "wrong-password"),
                headers={"X-Forwarded-For": "203.0.113.10"},
            )
        assert response.status_code == 429

        other_ip = client.post(
            "/auth/login",
            data=login_form("nobody@brasaland.com", "wrong-password"),
            headers={"X-Forwarded-For": "203.0.113.11"},
        )
        assert other_ip.status_code == 401
    finally:
        limiter.enabled = was
