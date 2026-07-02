from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("JWT_ALGORITHM", "RS256")

import database
import models  # noqa: F401

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
PUBLIC_PEM = _key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

os.environ.setdefault("JWT_PUBLIC_KEY", PUBLIC_PEM)

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


def make_access_token(user_id: int) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=30)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "exp": int(expire_at.timestamp()),
    }
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256")


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_PUBLIC_KEY", PUBLIC_PEM)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")


@pytest.fixture(autouse=True)
def _reset_db() -> Generator[None, None, None]:
    SQLModel.metadata.create_all(_test_engine)
    yield
    SQLModel.metadata.drop_all(_test_engine)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    with Session(_test_engine) as db_session:
        yield db_session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app import app

    def override_get_db() -> Generator[Session, None, None]:
        with Session(_test_engine) as db_session:
            yield db_session

    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
