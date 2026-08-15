from __future__ import annotations

import time
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from brasaland_auth_verify.deps import (
    get_current_user_uuid,
    get_optional_user_uuid,
    require_admin,
)
from brasaland_auth_verify.testing import generate_rsa_keypair, mint_access_token
from tests.conftest import PRIVATE_PEM

app = FastAPI()


@app.get("/whoami")
def whoami(
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, str]:
    return {"user": user_uuid}


@app.get("/maybe")
def maybe(
    user_uuid: Annotated[str | None, Depends(get_optional_user_uuid)],
) -> dict[str, str | None]:
    return {"user": user_uuid}


@app.get("/admin")
def admin(admin_uuid: Annotated[str, Depends(require_admin)]) -> dict[str, str]:
    return {"admin": admin_uuid}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _bearer(**mint_kwargs: object) -> dict[str, str]:
    token = mint_access_token(PRIVATE_PEM, **mint_kwargs)  # type: ignore[arg-type]
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_returns_401(client: TestClient) -> None:
    response = client.get("/whoami")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_garbage_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/whoami", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_valid_token_returns_identity(client: TestClient) -> None:
    response = client.get("/whoami", headers=_bearer(user_id=7))
    assert response.status_code == 200
    assert response.json() == {"user": "7"}


def test_sub_only_token_returns_identity(client: TestClient) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"sub": "42", "iat": now, "exp": now + 300},
        PRIVATE_PEM,
        algorithm="RS256",
    )
    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user": "42"}


def test_expired_token_returns_401(client: TestClient) -> None:
    response = client.get("/whoami", headers=_bearer(expires_in_seconds=-10))
    assert response.status_code == 401


def test_typed_token_rejected_as_access_token(client: TestClient) -> None:
    response = client.get("/whoami", headers=_bearer(token_type="refresh"))
    assert response.status_code == 401


def test_wrong_key_token_returns_401(client: TestClient) -> None:
    other_private, _ = generate_rsa_keypair()
    token = mint_access_token(other_private, user_id=7)
    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_optional_identity_without_token_is_none(client: TestClient) -> None:
    response = client.get("/maybe")
    assert response.status_code == 200
    assert response.json() == {"user": None}


def test_optional_identity_with_token(client: TestClient) -> None:
    response = client.get("/maybe", headers=_bearer(user_id=9))
    assert response.status_code == 200
    assert response.json() == {"user": "9"}


def test_optional_identity_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/maybe", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401


def test_require_admin_rejects_non_admin(client: TestClient) -> None:
    response = client.get("/admin", headers=_bearer(user_id=7, is_admin=False))
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_require_admin_accepts_admin(client: TestClient) -> None:
    response = client.get("/admin", headers=_bearer(user_id=3, is_admin=True))
    assert response.status_code == 200
    assert response.json() == {"admin": "3"}
