from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import app as app_module
from auth.security import create_access_token, decode_access_token
from auth.service import (
    PASSWORD_RESET_TOKEN_TYPE,
    ensure_bootstrap_admin,
    register_user as register_user_service,
    update_user,
)
from tests.helpers import assign_test_location, login_form


@pytest.fixture
def client() -> TestClient:
    with TestClient(app_module.app) as test_client:
        yield test_client


def _assert_no_hashed_password(data: Any) -> None:
    if isinstance(data, dict):
        assert "hashed_password" not in data
        for value in data.values():
            _assert_no_hashed_password(value)
    elif isinstance(data, list):
        for item in data:
            _assert_no_hashed_password(item)


def _register(client: TestClient, email: str, password: str) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    _assert_no_hashed_password(response.json())
    return response.json()


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(
    client: TestClient, email: str = "admin@brasaland.com"
) -> dict[str, str]:
    register_user_service(email, "password123", is_admin=True)
    login = client.post(
        "/auth/login",
        data=login_form(email, "password123"),
    )
    assert login.status_code == 200
    return _auth_header(login.json()["access_token"])


def test_register_returns_token_and_me_shows_email(client: TestClient) -> None:
    token_payload = _register(client, "ops@brasaland.com", "password123")
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]
    assert token_payload["refresh_token"]

    me_response = client.get(
        "/auth/me",
        headers=_auth_header(token_payload["access_token"]),
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "ops@brasaland.com"
    _assert_no_hashed_password(me_data)


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_garbage_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers=_auth_header("not.a.valid.token"),
    )
    assert response.status_code == 401


def test_login_success_and_wrong_password(client: TestClient) -> None:
    _register(client, "login@brasaland.com", "password123")
    assign_test_location("login@brasaland.com")

    success = client.post(
        "/auth/login",
        data=login_form("login@brasaland.com", "password123"),
    )
    assert success.status_code == 200
    _assert_no_hashed_password(success.json())
    assert success.json()["access_token"]
    assert success.json()["refresh_token"]

    failure = client.post(
        "/auth/login",
        data=login_form("login@brasaland.com", "wrong-password"),
    )
    assert failure.status_code == 401


def test_normal_user_cannot_delete_other_user(client: TestClient) -> None:
    first = _register(client, "first@brasaland.com", "password123")
    second = _register(client, "second@brasaland.com", "password123")

    second_me = client.get(
        "/auth/me",
        headers=_auth_header(second["access_token"]),
    ).json()

    response = client.delete(
        f"/users/{second_me['id']}",
        headers=_auth_header(first["access_token"]),
    )
    assert response.status_code == 403


def test_normal_user_cannot_update_other_user(client: TestClient) -> None:
    first = _register(client, "update-first@brasaland.com", "password123")
    second = _register(client, "update-second@brasaland.com", "password123")

    second_me = client.get(
        "/auth/me",
        headers=_auth_header(second["access_token"]),
    ).json()

    response = client.put(
        f"/users/{second_me['id']}",
        headers=_auth_header(first["access_token"]),
        json={"password": "newpassword1"},
    )
    assert response.status_code == 403


def test_normal_user_cannot_list_users(client: TestClient) -> None:
    alice = _register(client, "alice@brasaland.com", "password123")

    response = client.get("/users", headers=_auth_header(alice["access_token"]))

    assert response.status_code == 403
    assert response.json()["detail"] == app_module.ADMIN_REQUIRED


def test_admin_lists_users_with_emails(client: TestClient) -> None:
    _register(client, "bob@brasaland.com", "password123")
    headers = _admin_headers(client)

    response = client.get("/users", headers=headers)

    assert response.status_code == 200
    users = response.json()
    _assert_no_hashed_password(users)
    emails = {user["email"] for user in users}
    assert "bob@brasaland.com" in emails
    assert "admin@brasaland.com" in emails


def test_non_admin_cannot_read_other_user(client: TestClient) -> None:
    first = _register(client, "read-first@brasaland.com", "password123")
    second = _register(client, "read-second@brasaland.com", "password123")

    second_me = client.get(
        "/auth/me",
        headers=_auth_header(second["access_token"]),
    ).json()

    response = client.get(
        f"/users/{second_me['id']}",
        headers=_auth_header(first["access_token"]),
    )
    assert response.status_code == 403


def test_admin_can_read_other_user(client: TestClient) -> None:
    user = _register(client, "readable@brasaland.com", "password123")
    user_me = client.get(
        "/auth/me",
        headers=_auth_header(user["access_token"]),
    ).json()
    headers = _admin_headers(client)

    response = client.get(f"/users/{user_me['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "readable@brasaland.com"


def test_normal_user_cannot_set_is_admin_via_put(client: TestClient) -> None:
    token_payload = _register(client, "self@brasaland.com", "password123")
    me = client.get(
        "/auth/me",
        headers=_auth_header(token_payload["access_token"]),
    ).json()
    assert me["is_admin"] is False

    response = client.put(
        f"/users/{me['id']}",
        headers=_auth_header(token_payload["access_token"]),
        json={"password": "newpassword1", "is_admin": True},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["is_admin"] is False
    _assert_no_hashed_password(updated)


def test_update_email_rejects_duplicate_but_allows_fresh_and_own(client: TestClient) -> None:
    _register(client, "a@x.com", "password123")
    user_b = _register(client, "b@x.com", "password123")

    b_me = client.get(
        "/auth/me",
        headers=_auth_header(user_b["access_token"]),
    ).json()
    b_headers = _auth_header(user_b["access_token"])

    taken = client.put(
        f"/users/{b_me['id']}",
        headers=b_headers,
        json={"email": "A@X.com"},
    )
    assert taken.status_code == 400

    updated = client.put(
        f"/users/{b_me['id']}",
        headers=b_headers,
        json={"email": "fresh@x.com"},
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "fresh@x.com"

    same_email = client.put(
        f"/users/{b_me['id']}",
        headers=b_headers,
        json={"email": "Fresh@X.com"},
    )
    assert same_email.status_code == 200
    assert same_email.json()["email"] == "fresh@x.com"


def test_hashed_password_never_appears_in_responses(client: TestClient) -> None:
    headers = _admin_headers(client, "leak-admin@brasaland.com")

    me = client.get("/auth/me", headers=headers)
    users = client.get("/users", headers=headers)
    single = client.get(f"/users/{me.json()['id']}", headers=headers)

    for response in (me, users, single):
        assert response.status_code == 200
        _assert_no_hashed_password(response.json())

    login = client.post(
        "/auth/login",
        data=login_form("leak-admin@brasaland.com", "password123"),
    )
    assert login.status_code == 200
    _assert_no_hashed_password(login.json())

    created = client.post(
        "/users",
        headers=headers,
        json={"email": "created@brasaland.com", "password": "password123"},
    )
    assert created.status_code == 201
    _assert_no_hashed_password(created.json())


def test_non_admin_cannot_create_user(client: TestClient) -> None:
    token_payload = _register(client, "plain@brasaland.com", "password123")

    response = client.post(
        "/users",
        headers=_auth_header(token_payload["access_token"]),
        json={"email": "minted@brasaland.com", "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == app_module.ADMIN_REQUIRED


def test_admin_can_create_user_including_admins(client: TestClient) -> None:
    headers = _admin_headers(client)

    created = client.post(
        "/users",
        headers=headers,
        json={"email": "minted@brasaland.com", "password": "password123"},
    )
    assert created.status_code == 201
    assert created.json()["is_admin"] is False

    minted_admin = client.post(
        "/users",
        headers=headers,
        json={
            "email": "minted-admin@brasaland.com",
            "password": "password123",
            "is_admin": True,
        },
    )
    assert minted_admin.status_code == 201
    assert minted_admin.json()["is_admin"] is True


def test_users_routes_require_token(client: TestClient) -> None:
    assert client.get("/users").status_code == 401
    response = client.post(
        "/users",
        json={"email": "anon@brasaland.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_register_duplicate_email_returns_named_constant(client: TestClient) -> None:
    _register(client, "dup@brasaland.com", "password123")

    response = client.post(
        "/auth/register",
        json={"email": "dup@brasaland.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == app_module.EMAIL_ALREADY_REGISTERED


def test_register_disabled_returns_403(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AUTH_ALLOW_SELF_REGISTER", "false")

    response = client.post(
        "/auth/register",
        json={"email": "gate@brasaland.com", "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == app_module.SELF_REGISTRATION_DISABLED


def test_read_missing_user_returns_named_constant(client: TestClient) -> None:
    headers = _admin_headers(client, "reader-admin@brasaland.com")

    response = client.get("/users/9999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == app_module.USER_NOT_FOUND


def test_delete_missing_user_returns_named_constant(client: TestClient) -> None:
    admin = register_user_service(
        "admin-delete@brasaland.com",
        "password123",
        is_admin=True,
    )
    admin_token = create_access_token(
        {"sub": str(admin["id"]), "user_id": admin["id"]},
    )
    headers = _auth_header(admin_token)

    response = client.delete("/users/9999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == app_module.USER_NOT_FOUND


def test_inactive_user_cannot_access_protected_route(client: TestClient) -> None:
    token_payload = _register(client, "inactive@brasaland.com", "password123")
    headers = _auth_header(token_payload["access_token"])
    me = client.get("/auth/me", headers=headers).json()

    update_user(me["id"], {"is_active": False})

    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


def test_empty_update_returns_current_user_without_changes(
    client: TestClient,
) -> None:
    token_payload = _register(client, "empty-update@brasaland.com", "password123")
    headers = _auth_header(token_payload["access_token"])
    me = client.get("/auth/me", headers=headers).json()

    response = client.put(f"/users/{me['id']}", headers=headers, json={})

    assert response.status_code == 200
    assert response.json()["email"] == me["email"]
    assert response.json()["is_active"] is True


def test_me_accepts_token_with_sub_only_claim(client: TestClient) -> None:
    token_payload = _register(client, "subonly@brasaland.com", "password123")
    me = client.get(
        "/auth/me",
        headers=_auth_header(token_payload["access_token"]),
    ).json()

    sub_only_token = create_access_token({"sub": str(me["id"])})
    response = client.get("/auth/me", headers=_auth_header(sub_only_token))

    assert response.status_code == 200
    assert response.json()["email"] == "subonly@brasaland.com"


def test_access_token_carries_is_admin_claim(client: TestClient) -> None:
    token_payload = _register(client, "claim@brasaland.com", "password123")
    assert decode_access_token(token_payload["access_token"])["is_admin"] is False

    headers = _admin_headers(client, "claim-admin@brasaland.com")
    admin_token = headers["Authorization"].removeprefix("Bearer ")
    assert decode_access_token(admin_token)["is_admin"] is True


def test_static_pages_are_served(client: TestClient) -> None:
    for path in ("/", "/forgot-password", "/reset-password"):
        response = client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


def test_refresh_returns_new_working_access_token(client: TestClient) -> None:
    token_payload = _register(client, "refresh-api@brasaland.com", "password123")
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": token_payload["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    me_response = client.get(
        "/auth/me",
        headers=_auth_header(refreshed["access_token"]),
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "refresh-api@brasaland.com"


def test_refresh_rotates_refresh_token(client: TestClient) -> None:
    token_payload = _register(client, "refresh-rotate-api@brasaland.com", "password123")
    old_refresh = token_payload["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_response.status_code == 200
    new_refresh = refresh_response.json()["refresh_token"]
    assert new_refresh != old_refresh

    stale_response = client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert stale_response.status_code == 401
    assert stale_response.json()["detail"] == app_module.INVALID_REFRESH_TOKEN


def test_refresh_rejects_garbage_token(client: TestClient) -> None:
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == app_module.INVALID_REFRESH_TOKEN


def test_refresh_rejects_access_token(client: TestClient) -> None:
    token_payload = _register(client, "refresh-access-api@brasaland.com", "password123")
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": token_payload["access_token"]},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == app_module.INVALID_REFRESH_TOKEN


def test_refresh_token_rejected_as_bearer_access_token(client: TestClient) -> None:
    token_payload = _register(client, "refresh-bearer-api@brasaland.com", "password123")
    response = client.get(
        "/auth/me",
        headers=_auth_header(token_payload["refresh_token"]),
    )
    assert response.status_code == 401


def test_password_reset_token_rejected_as_bearer_access_token(
    client: TestClient,
) -> None:
    token_payload = _register(client, "reset-bearer-api@brasaland.com", "password123")
    me = client.get(
        "/auth/me",
        headers=_auth_header(token_payload["access_token"]),
    ).json()

    reset_token = create_access_token(
        {
            "sub": str(me["id"]),
            "user_id": me["id"],
            "type": PASSWORD_RESET_TOKEN_TYPE,
        },
    )
    response = client.get("/auth/me", headers=_auth_header(reset_token))
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    token_payload = _register(client, "logout-api@brasaland.com", "password123")
    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": token_payload["refresh_token"]},
    )
    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": token_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == app_module.INVALID_REFRESH_TOKEN


def test_logout_is_idempotent_for_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/auth/logout",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 204


def test_get_profiles_me_returns_email_and_profile_fields(client: TestClient) -> None:
    token_payload = _register(client, "profile-get@brasaland.com", "password123")

    response = client.get(
        "/auth/profiles/me",
        headers=_auth_header(token_payload["access_token"]),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile-get@brasaland.com"
    assert data["name"] == ""
    assert data["phone"] == ""
    assert data["address"] == ""
    _assert_no_hashed_password(data)


def test_put_profiles_me_updates_and_returns_new_values(client: TestClient) -> None:
    token_payload = _register(client, "profile-put@brasaland.com", "password123")

    response = client.put(
        "/auth/profiles/me",
        headers=_auth_header(token_payload["access_token"]),
        json={
            "name": "Settar Mengli",
            "phone": "+57 300 000 0000",
            "address": "Medellín, Colombia",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile-put@brasaland.com"
    assert data["name"] == "Settar Mengli"
    assert data["phone"] == "+57 300 000 0000"
    assert data["address"] == "Medellín, Colombia"
    _assert_no_hashed_password(data)

    get_response = client.get(
        "/auth/profiles/me",
        headers=_auth_header(token_payload["access_token"]),
    )
    assert get_response.status_code == 200
    assert get_response.json() == data


def test_profiles_me_without_token_returns_401(client: TestClient) -> None:
    get_response = client.get("/auth/profiles/me")
    assert get_response.status_code == 401

    put_response = client.put(
        "/auth/profiles/me",
        json={"name": "Nope"},
    )
    assert put_response.status_code == 401


def test_put_profiles_me_ignores_email_password_and_flags(client: TestClient) -> None:
    token_payload = _register(client, "profile-secure@brasaland.com", "password123")
    headers = _auth_header(token_payload["access_token"])

    before = client.get("/auth/me", headers=headers).json()
    assert before["email"] == "profile-secure@brasaland.com"
    assert before["is_admin"] is False
    assert before["is_active"] is True

    response = client.put(
        "/auth/profiles/me",
        headers=headers,
        json={
            "name": "Safe Name",
            "phone": "555",
            "address": "Calle 1",
            "email": "attacker@evil.com",
            "password": "hijacked-password",
            "is_admin": True,
            "is_active": False,
        },
    )
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == "profile-secure@brasaland.com"
    assert profile["name"] == "Safe Name"
    assert profile["phone"] == "555"
    assert profile["address"] == "Calle 1"

    after = client.get("/auth/me", headers=headers).json()
    assert after["email"] == "profile-secure@brasaland.com"
    assert after["is_admin"] is False
    assert after["is_active"] is True
    assert after["name"] == "Safe Name"

    assign_test_location("profile-secure@brasaland.com")

    login = client.post(
        "/auth/login",
        data=login_form("profile-secure@brasaland.com", "password123"),
    )
    assert login.status_code == 200

    hijack_login = client.post(
        "/auth/login",
        data=login_form("profile-secure@brasaland.com", "hijacked-password"),
    )
    assert hijack_login.status_code == 401


def test_bootstrap_admin_seeded_on_startup_when_store_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_BOOTSTRAP_ADMIN_EMAIL", "boot@brasaland.com")
    monkeypatch.setenv("AUTH_BOOTSTRAP_ADMIN_PASSWORD", "password123")

    with TestClient(app_module.app) as test_client:
        login = test_client.post(
            "/auth/login",
            data=login_form("boot@brasaland.com", "password123"),
        )
        assert login.status_code == 200
        me = test_client.get(
            "/auth/me",
            headers=_auth_header(login.json()["access_token"]),
        ).json()
        assert me["is_admin"] is True


def test_bootstrap_admin_skipped_when_users_exist(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register(client, "existing@brasaland.com", "password123")
    monkeypatch.setenv("AUTH_BOOTSTRAP_ADMIN_EMAIL", "boot@brasaland.com")
    monkeypatch.setenv("AUTH_BOOTSTRAP_ADMIN_PASSWORD", "password123")

    assert ensure_bootstrap_admin() is None


def test_bootstrap_admin_requires_both_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_BOOTSTRAP_ADMIN_EMAIL", "boot@brasaland.com")
    monkeypatch.delenv("AUTH_BOOTSTRAP_ADMIN_PASSWORD", raising=False)

    assert ensure_bootstrap_admin() is None
