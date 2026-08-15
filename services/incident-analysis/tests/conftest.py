from __future__ import annotations

import pytest
from brasaland_auth_verify.testing import generate_rsa_keypair, mint_access_token

from result_store import result_store

_PRIVATE_PEM, _PUBLIC_PEM = generate_rsa_keypair()


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_PUBLIC_KEY", _PUBLIC_PEM)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("ANALYSIS_RESULT_TTL_SECONDS", "3600")


@pytest.fixture(autouse=True)
def clear_result_store() -> None:
    result_store.clear()
    yield
    result_store.clear()


@pytest.fixture(autouse=True)
def disable_rate_limits() -> None:
    from app import app

    limiter = getattr(app.state, "limiter", None)
    if limiter is None:
        yield
        return
    was = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was


@pytest.fixture
def access_token() -> str:
    return mint_access_token(_PRIVATE_PEM, user_id=1)


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mint_headers() -> object:
    def _mint(*, user_id: int = 1, is_admin: bool = False) -> dict[str, str]:
        token = mint_access_token(
            _PRIVATE_PEM, user_id=user_id, is_admin=is_admin
        )
        return {"Authorization": f"Bearer {token}"}

    return _mint


@pytest.fixture
def client(auth_headers: dict[str, str]):
    from fastapi.testclient import TestClient

    import app as app_module

    with TestClient(app_module.app, headers=auth_headers) as test_client:
        yield test_client
