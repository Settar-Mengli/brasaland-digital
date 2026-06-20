from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from auth.repository import (
    create_user,
    delete_user as delete_user_record,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user as update_user_record,
)
from auth.security import hash_password, verify_password
from auth.types import EmailAlreadyExistsError, UserNotFoundError, UserRecord


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(
    email: str,
    password: str,
    is_admin: bool = False,
) -> UserRecord:
    normalized_email = _normalize_email(email)
    if get_user_by_email(normalized_email) is not None:
        raise EmailAlreadyExistsError(
            f"Email already registered: {normalized_email}"
        )

    return create_user(
        {
            "email": normalized_email,
            "hashed_password": hash_password(password),
            "is_active": True,
            "is_admin": is_admin,
            "created_at": _utc_now_iso(),
        }
    )


def authenticate_user(email: str, password: str) -> UserRecord | None:
    user = get_user_by_email(_normalize_email(email))
    if user is None:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_user(user_id: int) -> UserRecord:
    user = get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundError(f"User not found: {user_id}")
    return user


def list_all_users() -> list[UserRecord]:
    return list_users()


def update_user(user_id: int, fields: dict[str, Any]) -> UserRecord:
    user = update_user_record(user_id, fields)
    if user is None:
        raise UserNotFoundError(f"User not found: {user_id}")
    return user


def delete_user(user_id: int) -> None:
    if not delete_user_record(user_id):
        raise UserNotFoundError(f"User not found: {user_id}")
