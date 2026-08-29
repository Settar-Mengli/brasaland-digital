"""Location-scoped JWT claims and user assignment tests."""

from __future__ import annotations

import app as app_module
import pytest
from auth.security import decode_access_token
from auth.service import (
    issue_token_pair,
    rotate_refresh_token,
)
from auth.service import (
    register_user as register_user_service,
)
from auth.types import InvalidRefreshTokenError
from fastapi.testclient import TestClient

from tests.helpers import TEST_LOCATION_SLUG, login_form


@pytest.fixture
def client() -> TestClient:
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_scoped_user_login_jwt_contains_location_claims(client: TestClient) -> None:
    email = "scoped-claims@brasaland.com"
    register_user_service(
        email,
        "password123",
        authorized_locations=["medellin_centro", "bogota_chapinero"],
    )

    response = client.post(
        "/auth/login",
        data=login_form(email, "password123", "bogota_chapinero"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["location_slug"] == "bogota_chapinero"

    claims = decode_access_token(payload["access_token"])
    assert claims["authorized_locations"] == ["bogota_chapinero", "medellin_centro"]
    assert claims["location_slug"] == "bogota_chapinero"
    assert claims["is_admin"] is False
    assert claims["location_slug"] == "bogota_chapinero"
    assert "bogota_chapinero" in claims["authorized_locations"]


def test_admin_login_jwt_has_empty_authorized_locations(client: TestClient) -> None:
    email = "admin-claims@brasaland.com"
    register_user_service(email, "password123", is_admin=True)

    response = client.post(
        "/auth/login",
        data=login_form(email, "password123", "miami_brickell"),
    )
    assert response.status_code == 200
    claims = decode_access_token(response.json()["access_token"])
    assert claims["is_admin"] is True
    assert claims["authorized_locations"] == []
    assert claims["location_slug"] == "miami_brickell"


def test_login_rejects_unauthorized_location_slug(client: TestClient) -> None:
    email = "scoped-deny@brasaland.com"
    register_user_service(
        email,
        "password123",
        authorized_locations=["medellin_centro"],
    )

    response = client.post(
        "/auth/login",
        data=login_form(email, "password123", "bogota_chapinero"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == app_module.LOCATION_NOT_AUTHORIZED


def test_scoped_user_without_assignment_cannot_preflight_or_login(
    client: TestClient,
) -> None:
    email = "no-assignment@brasaland.com"
    register_user_service(email, "password123")

    preflight = client.post(
        "/auth/login/authorized-locations",
        json={"email": email, "password": "password123"},
    )
    assert preflight.status_code == 403
    assert preflight.json()["detail"] == app_module.NO_LOCATION_ASSIGNED

    login = client.post(
        "/auth/login",
        data=login_form(email, "password123"),
    )
    assert login.status_code == 403
    assert login.json()["detail"] == app_module.NO_LOCATION_ASSIGNED


def test_preflight_returns_authorized_locations_for_scoped_user(
    client: TestClient,
) -> None:
    email = "preflight-scoped@brasaland.com"
    register_user_service(
        email,
        "password123",
        authorized_locations=["medellin_centro", "bogota_chapinero"],
    )

    response = client.post(
        "/auth/login/authorized-locations",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_admin"] is False
    assert body["authorized_locations"] == ["bogota_chapinero", "medellin_centro"]


def test_preflight_admin_returns_all_canonical_slugs(client: TestClient) -> None:
    email = "preflight-admin@brasaland.com"
    register_user_service(email, "password123", is_admin=True)

    response = client.post(
        "/auth/login/authorized-locations",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_admin"] is True
    assert len(body["authorized_locations"]) == 14
    assert TEST_LOCATION_SLUG in body["authorized_locations"]


def test_refresh_preserves_location_slug_in_access_token(client: TestClient) -> None:
    user = register_user_service(
        "refresh-location@brasaland.com",
        "password123",
        authorized_locations=["medellin_centro"],
    )
    access_token, refresh_token = issue_token_pair(user, TEST_LOCATION_SLUG)
    new_access, new_refresh = rotate_refresh_token(refresh_token)

    access_claims = decode_access_token(new_access)
    assert access_claims["location_slug"] == TEST_LOCATION_SLUG
    refresh_claims = decode_access_token(new_refresh)
    assert refresh_claims["location_slug"] == TEST_LOCATION_SLUG
    assert new_refresh != refresh_token


def test_refresh_fails_when_location_assignment_revoked() -> None:
    email = "refresh-revoked-loc@brasaland.com"
    user = register_user_service(
        email,
        "password123",
        authorized_locations=["medellin_centro"],
    )
    _, refresh_token = issue_token_pair(user, TEST_LOCATION_SLUG)

    from auth.service import update_user

    update_user(user["id"], {"authorized_locations": ["bogota_chapinero"]})

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(refresh_token)


def test_admin_can_create_user_with_authorized_locations(client: TestClient) -> None:
    register_user_service("creator-admin@brasaland.com", "password123", is_admin=True)
    login = client.post(
        "/auth/login",
        data=login_form("creator-admin@brasaland.com", "password123"),
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = client.post(
        "/users",
        headers=headers,
        json={
            "email": "assigned-user@brasaland.com",
            "password": "password123",
            "authorized_locations": ["medellin_centro", "bogota_chapinero"],
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["authorized_locations"] == ["bogota_chapinero", "medellin_centro"]


def test_admin_can_update_user_authorized_locations(client: TestClient) -> None:
    register_user_service("updater-admin@brasaland.com", "password123", is_admin=True)
    login = client.post(
        "/auth/login",
        data=login_form("updater-admin@brasaland.com", "password123"),
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    target = register_user_service(
        "target-user@brasaland.com",
        "password123",
        authorized_locations=["medellin_centro"],
    )

    response = client.put(
        f"/users/{target['id']}",
        headers=headers,
        json={"authorized_locations": ["bogota_chapinero"]},
    )
    assert response.status_code == 200
    assert response.json()["authorized_locations"] == ["bogota_chapinero"]


def test_non_admin_cannot_update_authorized_locations(client: TestClient) -> None:
    token_payload = client.post(
        "/auth/register",
        json={"email": "plain-updater@brasaland.com", "password": "password123"},
    ).json()
    headers = {"Authorization": f"Bearer {token_payload['access_token']}"}
    me = client.get("/auth/me", headers=headers).json()

    response = client.put(
        f"/users/{me['id']}",
        headers=headers,
        json={"authorized_locations": ["medellin_centro"]},
    )
    assert response.status_code == 403
