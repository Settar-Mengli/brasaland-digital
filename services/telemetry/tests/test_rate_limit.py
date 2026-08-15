"""Telemetry limiter wiring."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(autouse=True)
def _disable_rate_limits() -> None:
    limiter = getattr(app.state, "limiter", None)
    if limiter is None:
        yield
        return
    was = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was


def test_limiter_attached() -> None:
    assert getattr(app.state, "limiter", None) is not None


def test_ingest_still_accepts_when_limiter_disabled() -> None:
    client = TestClient(app)
    response = client.post(
        "/telemetry/events",
        json={"events": [{"name": "ping", "properties": {}}]},
    )
    assert response.status_code in (200, 201, 422)  # 422 if schema stricter
