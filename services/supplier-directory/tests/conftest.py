from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brasaland_auth_verify.testing import generate_rsa_keypair, mint_access_token

from supplier_directory.db import get_db, reset_db

_PRIVATE_PEM, _PUBLIC_PEM = generate_rsa_keypair()


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
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "suppliers.json"
    monkeypatch.setenv("SUPPLIER_DB_PATH", str(db_path))
    reset_db()
    get_db()
    yield
    reset_db()
