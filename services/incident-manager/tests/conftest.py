from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

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

import incident_manager.database as database
import incident_manager.models  # noqa: F401

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
    return mint_access_token(_PRIVATE_PEM, user_id=1)


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def isolated_db() -> Generator[None, None, None]:
    database._schema_ready = False
    SQLModel.metadata.create_all(database.engine)
    yield
    SQLModel.metadata.drop_all(database.engine)
    database._schema_ready = False
