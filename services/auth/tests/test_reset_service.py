from __future__ import annotations

import pytest

from auth.repository import get_user_by_email
from auth.security import TokenError, create_access_token
from auth.service import (
    PASSWORD_RESET_TOKEN_TYPE,
    authenticate_user,
    register_user,
    request_password_reset,
    reset_password,
)
from auth.types import InvalidResetTokenError


def test_request_password_reset_stores_hashed_token_for_known_email() -> None:
    register_user("reset-known@brasaland.com", "old-password1")
    user_before = get_user_by_email("reset-known@brasaland.com")
    assert user_before is not None
    assert user_before.get("reset_token_hash") is None

    token = request_password_reset("reset-known@brasaland.com")
    assert token is not None

    user_after = get_user_by_email("reset-known@brasaland.com")
    assert user_after is not None
    assert user_after.get("reset_token_hash") is not None
    assert user_after.get("reset_token_hash") != token
    assert user_after.get("reset_token_expires") is not None


def test_request_password_reset_unknown_email_returns_none() -> None:
    result = request_password_reset("missing@brasaland.com")
    assert result is None


def test_reset_password_updates_password_and_clears_reset_hash() -> None:
    register_user("reset-flow@brasaland.com", "old-password1")
    token = request_password_reset("reset-flow@brasaland.com")
    assert token is not None

    reset_password(token, "new-password1")

    user = get_user_by_email("reset-flow@brasaland.com")
    assert user is not None
    assert user.get("reset_token_hash") is None
    assert user.get("reset_token_expires") is None
    assert authenticate_user("reset-flow@brasaland.com", "new-password1") is not None
    assert authenticate_user("reset-flow@brasaland.com", "old-password1") is None


def test_reset_password_rejects_reused_token() -> None:
    register_user("reset-reuse@brasaland.com", "old-password1")
    token = request_password_reset("reset-reuse@brasaland.com")
    assert token is not None

    reset_password(token, "new-password1")

    with pytest.raises(InvalidResetTokenError):
        reset_password(token, "another-pass1")


def test_reset_password_rejects_expired_token() -> None:
    register_user("reset-expired@brasaland.com", "old-password1")
    user = get_user_by_email("reset-expired@brasaland.com")
    assert user is not None

    expired_token = create_access_token(
        {
            "sub": str(user["id"]),
            "user_id": user["id"],
            "type": PASSWORD_RESET_TOKEN_TYPE,
        },
        expires_minutes=-1,
    )

    with pytest.raises(TokenError):
        reset_password(expired_token, "new-password1")


def test_reset_password_rejects_login_token() -> None:
    register_user("reset-type@brasaland.com", "old-password1")
    user = get_user_by_email("reset-type@brasaland.com")
    assert user is not None

    login_token = create_access_token(
        {"sub": str(user["id"]), "user_id": user["id"]},
        expires_minutes=30,
    )

    with pytest.raises(InvalidResetTokenError):
        reset_password(login_token, "new-password1")


def test_reset_token_hash_differs_for_distinct_full_tokens() -> None:
    from auth.service import _hash_reset_token

    shared_prefix = "x" * 100
    token_a = shared_prefix + "first-distinct-reset-token-suffix"
    token_b = shared_prefix + "second-distinct-reset-token-suffix"

    assert _hash_reset_token(token_a) != _hash_reset_token(token_b)
