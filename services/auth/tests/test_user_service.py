from __future__ import annotations

import pytest

from auth.security import verify_password
from auth.service import (
    authenticate_user,
    delete_user,
    get_user,
    list_all_users,
    register_user,
    update_user,
)
from auth.types import EmailAlreadyExistsError, UserNotFoundError


def test_register_user_stores_hashed_password() -> None:
    plain = "secure-test-password"
    user = register_user("ops@brasaland.com", plain)

    assert user["hashed_password"] != plain
    assert verify_password(plain, user["hashed_password"]) is True
    assert user["is_active"] is True
    assert user["is_admin"] is False
    assert user["created_at"]


def test_register_user_rejects_duplicate_email() -> None:
    register_user("duplicate@brasaland.com", "password-one")

    with pytest.raises(EmailAlreadyExistsError):
        register_user("duplicate@brasaland.com", "password-two")


def test_email_is_normalized_for_lookup_and_storage() -> None:
    user = register_user("Ops@Brasaland.com", "password")

    authenticated = authenticate_user("ops@brasaland.com", "password")
    assert authenticated is not None
    assert authenticated["id"] == user["id"]
    assert authenticated["email"] == "ops@brasaland.com"

    with pytest.raises(EmailAlreadyExistsError):
        register_user("OPS@BRASALAND.COM", "other-password")


def test_authenticate_user_success_and_failures() -> None:
    register_user("known@brasaland.com", "correct-password")

    authenticated = authenticate_user("known@brasaland.com", "correct-password")
    assert authenticated is not None
    assert authenticated["email"] == "known@brasaland.com"

    assert authenticate_user("known@brasaland.com", "wrong-password") is None
    assert authenticate_user("missing@brasaland.com", "any-password") is None


def test_get_list_update_delete_users() -> None:
    first = register_user("first@brasaland.com", "password-a", is_admin=False)
    second = register_user("second@brasaland.com", "password-b", is_admin=True)

    fetched = get_user(first["id"])
    assert fetched["email"] == "first@brasaland.com"

    all_users = list_all_users()
    assert len(all_users) == 2
    assert all_users[0]["id"] == first["id"]
    assert all_users[1]["id"] == second["id"]

    updated = update_user(second["id"], {"is_active": False})
    assert updated["is_active"] is False

    delete_user(first["id"])

    with pytest.raises(UserNotFoundError):
        get_user(first["id"])

    with pytest.raises(UserNotFoundError):
        delete_user(first["id"])
