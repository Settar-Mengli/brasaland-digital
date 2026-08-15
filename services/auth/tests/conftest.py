from __future__ import annotations

import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth.db import get_db, reset_db

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIVATE_PEM = _key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
_PUBLIC_PEM = _key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


@pytest.fixture(autouse=True)
def isolated_auth_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "users.json"
    monkeypatch.setenv("AUTH_DB_PATH", str(db_path))
    reset_db()
    get_db()
    yield
    reset_db()


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_PRIVATE_KEY", _PRIVATE_PEM)
    monkeypatch.setenv("JWT_PUBLIC_KEY", _PUBLIC_PEM)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("RESET_TOKEN_EXPIRE_MINUTES", "30")


@pytest.fixture(autouse=True)
def registration_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests exercise open self-registration unless a test overrides the gate."""
    monkeypatch.setenv("AUTH_ALLOW_SELF_REGISTER", "true")
    monkeypatch.delenv("AUTH_BOOTSTRAP_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("AUTH_BOOTSTRAP_ADMIN_PASSWORD", raising=False)


@pytest.fixture(autouse=True)
def disable_rate_limits() -> None:
    from app import app

    limiter = getattr(app.state, "limiter", None)
    if limiter is not None:
        was = limiter.enabled
        limiter.enabled = False
        yield
        limiter.enabled = was
    else:
        yield

