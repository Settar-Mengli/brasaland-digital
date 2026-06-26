from __future__ import annotations

import pytest

from auth.repository import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
)
from auth.security import hash_password


def _sample_record(email: str, user_id: int | None = None) -> dict[str, object]:
    record: dict[str, object] = {
        "email": email,
        "hashed_password": hash_password("password123"),
        "is_active": True,
        "is_admin": False,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    if user_id is not None:
        record["id"] = user_id
    return record


def test_get_user_by_id_returns_none_for_missing_user() -> None:
    assert get_user_by_id(9999) is None


def test_get_user_by_email_returns_none_for_missing_user() -> None:
    assert get_user_by_email("missing@brasaland.com") is None


def test_update_user_returns_none_when_user_missing() -> None:
    result = update_user(9999, {"is_active": False})
    assert result is None


def test_delete_user_returns_false_when_user_missing() -> None:
    assert delete_user(9999) is False


def test_next_id_starts_at_one_for_empty_table() -> None:
    first = create_user(_sample_record("first-id@brasaland.com"))
    assert first["id"] == 1
