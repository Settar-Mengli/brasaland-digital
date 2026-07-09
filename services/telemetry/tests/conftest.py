from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import app


def sample_event(**overrides: object) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "eventId": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sessionId": "session-abc",
        "userId": "42",
        "event_type": "ingredient_list_viewed",
        "schemaVersion": "2.0.0",
        "requestId": str(uuid4()),
        "service": "backoffice",
        "properties": {"location_id": "medellin_centro", "item_count": 3},
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
