"""Auth rate-limit coverage (login)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


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
                data={"username": "nobody@brasaland.com", "password": "wrong-password"},
            )
            codes.append(response.status_code)
        assert 429 in codes
        assert codes.count(401) >= 1
    finally:
        limiter.enabled = was
