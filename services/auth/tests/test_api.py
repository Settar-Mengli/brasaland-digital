from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import app as app_module


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


def test_register_returns_token_and_me_shows_email(client: TestClient) -> None:
    token_payload = _register(client, "ops@brasaland.com", "password123")
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]

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

    success = client.post(
        "/auth/login",
        data={"username": "login@brasaland.com", "password": "password123"},
    )
    assert success.status_code == 200
    _assert_no_hashed_password(success.json())
    assert success.json()["access_token"]

    failure = client.post(
        "/auth/login",
        data={"username": "login@brasaland.com", "password": "wrong-password"},
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


def test_list_users_hides_other_emails_for_normal_user(client: TestClient) -> None:
    alice = _register(client, "alice@brasaland.com", "password123")
    _register(client, "bob@brasaland.com", "password123")

    alice_me = client.get(
        "/auth/me",
        headers=_auth_header(alice["access_token"]),
    ).json()

    response = client.get("/users", headers=_auth_header(alice["access_token"]))
    assert response.status_code == 200
    users = response.json()
    _assert_no_hashed_password(users)

    by_id = {user["id"]: user for user in users}
    assert by_id[alice_me["id"]]["email"] == "alice@brasaland.com"

    other_ids = [user_id for user_id in by_id if user_id != alice_me["id"]]
    assert other_ids
    for other_id in other_ids:
        assert by_id[other_id]["email"] is None


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
    token_payload = _register(client, "leak@brasaland.com", "password123")
    headers = _auth_header(token_payload["access_token"])

    me = client.get("/auth/me", headers=headers)
    users = client.get("/users", headers=headers)
    single = client.get(f"/users/{me.json()['id']}", headers=headers)

    for response in (me, users, single):
        assert response.status_code == 200
        _assert_no_hashed_password(response.json())

    login = client.post(
        "/auth/login",
        data={"username": "leak@brasaland.com", "password": "password123"},
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
