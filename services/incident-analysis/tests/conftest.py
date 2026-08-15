from __future__ import annotations

import pytest
from brasaland_auth_verify.testing import generate_rsa_keypair, mint_access_token

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
