from __future__ import annotations

import os
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brasaland_auth_verify.testing import generate_rsa_keypair, mint_access_token

_PRIVATE_PEM, _PUBLIC_PEM = generate_rsa_keypair()

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("JWT_PUBLIC_KEY", _PUBLIC_PEM)
os.environ.setdefault("JWT_ALGORITHM", "RS256")

import database
import db_models  # noqa: F401
import cache

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


database.engine = _test_engine


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_PUBLIC_KEY", _PUBLIC_PEM)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")


@pytest.fixture
def access_token() -> str:
    return mint_access_token(_PRIVATE_PEM, user_id=7)


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def isolated_db() -> Generator[None, None, None]:
    allowlists = pytest.importorskip("allowlists")
    allowlists.load_allowlists.cache_clear()
    allowlists.load_allowed_property_keys.cache_clear()
    cache.clear_cache()

    database._schema_ready = False
    database.ensure_schema()
    yield
    SQLModel.metadata.drop_all(database.engine)
    database._schema_ready = False
    cache.clear_cache()


def seed_row(
    event_type: str,
    timestamp: datetime,
    tags: dict[str, object],
    *,
    event_id: str | None = None,
) -> None:
    from level import derive_level
    from repository import bulk_insert_events

    bulk_insert_events(
        [
            {
                "event_id": event_id or str(uuid4()),
                "event_type": event_type,
                "timestamp": timestamp,
                "service": "backoffice",
                "level": derive_level(event_type),
                "tags": tags,
                "context": {
                    "sessionId": "session-seed",
                    "userId": "42",
                    "requestId": str(uuid4()),
                    "schemaVersion": "2.1.0",
                },
            }
        ]
    )


def sample_event(**overrides: object) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "eventId": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sessionId": "session-abc",
        "userId": "42",
        "event_type": "ingredient_list_viewed",
        "schemaVersion": "2.1.0",
        "requestId": str(uuid4()),
        "service": "backoffice",
        "properties": {"location_id": "medellin_centro", "item_count": 3},
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client(auth_headers: dict[str, str]) -> Generator[Any, None, None]:
    from fastapi.testclient import TestClient

    from app import app

    with TestClient(
        app, raise_server_exceptions=False, headers=auth_headers
    ) as test_client:
        yield test_client
