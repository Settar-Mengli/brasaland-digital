from __future__ import annotations

import hashlib

import pytest

from auth.refresh_repository import get_by_hash
from auth.security import TokenError, decode_access_token
from auth.service import (
    REFRESH_TOKEN_TYPE,
    issue_refresh_token,
    issue_token_pair,
    register_user,
    resolve_active_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from auth.types import InvalidRefreshTokenError


def test_issue_refresh_token_stores_hashed_record() -> None:
    user = register_user("refresh-store@brasaland.com", "password123")
    token = issue_refresh_token(user)

    stored = get_by_hash(hashlib.sha256(token.encode()).hexdigest())
    assert stored is not None
    assert stored["user_id"] == user["id"]
    assert stored["revoked"] is False
    assert stored["token_hash"] != token


def test_issue_token_pair_returns_access_and_refresh() -> None:
    user = register_user("refresh-pair@brasaland.com", "password123")
    access_token, refresh_token = issue_token_pair(user)

    assert access_token
    assert refresh_token
    assert access_token != refresh_token


def test_rotate_refresh_token_issues_new_pair_and_revokes_old() -> None:
    user = register_user("refresh-rotate@brasaland.com", "password123")
    _, refresh_token = issue_token_pair(user)

    new_access, new_refresh = rotate_refresh_token(refresh_token)
    assert new_access
    assert new_refresh
    assert new_refresh != refresh_token

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(refresh_token)


def test_rotate_refresh_token_rejects_expired_token() -> None:
    user = register_user("refresh-expired@brasaland.com", "password123")
    expired_refresh = issue_refresh_token(user, expires_minutes=-1)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(expired_refresh)


def test_rotate_refresh_token_rejects_access_token() -> None:
    user = register_user("refresh-access@brasaland.com", "password123")
    access_token, _ = issue_token_pair(user)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(access_token)


def test_rotate_refresh_token_rejects_garbage_token() -> None:
    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token("not.a.valid.token")


def test_revoke_refresh_token_makes_rotation_fail() -> None:
    user = register_user("refresh-revoke@brasaland.com", "password123")
    _, refresh_token = issue_token_pair(user)

    revoke_refresh_token(refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(refresh_token)


def test_resolve_active_user_rejects_refresh_token() -> None:
    user = register_user("refresh-bearer@brasaland.com", "password123")
    _, refresh_token = issue_token_pair(user)

    assert resolve_active_user(refresh_token) is None


def test_resolve_active_user_accepts_access_token() -> None:
    user = register_user("refresh-access-ok@brasaland.com", "password123")
    access_token, _ = issue_token_pair(user)

    resolved = resolve_active_user(access_token)
    assert resolved is not None
    assert resolved["id"] == user["id"]


def test_refresh_token_has_refresh_type_claim() -> None:
    user = register_user("refresh-claim@brasaland.com", "password123")
    refresh_token = issue_refresh_token(user)

    payload = decode_access_token(refresh_token)
    assert payload.get("type") == REFRESH_TOKEN_TYPE


def test_rotate_refresh_token_rejects_tampered_token() -> None:
    user = register_user("refresh-tamper@brasaland.com", "password123")
    refresh_token = issue_refresh_token(user)
    header, payload_segment, signature = refresh_token.split(".")
    tampered_char = "a" if payload_segment[-1] != "a" else "b"
    tampered_token = ".".join(
        [header, payload_segment[:-1] + tampered_char, signature],
    )

    with pytest.raises((InvalidRefreshTokenError, TokenError)):
        rotate_refresh_token(tampered_token)
