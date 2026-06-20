from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from auth.repository import (
    create_user,
    delete_user as delete_user_record,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user as update_user_record,
)
from auth.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from auth.types import (
    EmailAlreadyExistsError,
    InvalidResetTokenError,
    UserNotFoundError,
    UserRecord,
)

PASSWORD_RESET_TOKEN_TYPE = "password_reset"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _reset_token_expire_minutes() -> int:
    return int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", "30"))


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _user_id_from_token_payload(payload: dict[str, Any]) -> int | None:
    if "user_id" in payload:
        return int(payload["user_id"])
    subject = payload.get("sub")
    if subject is None:
        return None
    return int(subject)


def request_password_reset(email: str) -> str | None:
    user = get_user_by_email(_normalize_email(email))
    if user is None:
        return None

    minutes = _reset_token_expire_minutes()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    token = create_access_token(
        {
            "sub": str(user["id"]),
            "user_id": user["id"],
            "type": PASSWORD_RESET_TOKEN_TYPE,
        },
        expires_minutes=minutes,
    )

    update_user_record(
        user["id"],
        {
            "reset_token_hash": _hash_reset_token(token),
            "reset_token_expires": expire_at.isoformat(),
        },
    )
    return token


def reset_password(token: str, new_password: str) -> None:
    try:
        payload = decode_access_token(token)
    except TokenError:
        raise

    if payload.get("type") != PASSWORD_RESET_TOKEN_TYPE:
        raise InvalidResetTokenError("Invalid password-reset token")

    user_id = _user_id_from_token_payload(payload)
    if user_id is None:
        raise InvalidResetTokenError("Invalid password-reset token")

    user = get_user_by_id(user_id)
    if user is None:
        raise InvalidResetTokenError("Invalid password-reset token")

    stored_hash = user.get("reset_token_hash")
    if stored_hash is None or not hmac.compare_digest(
        _hash_reset_token(token), stored_hash
    ):
        raise InvalidResetTokenError("Invalid password-reset token")

    update_user_record(
        user_id,
        {
            "hashed_password": hash_password(new_password),
            "reset_token_hash": None,
            "reset_token_expires": None,
        },
    )


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
    update_fields = dict(fields)

    if "email" in update_fields:
        normalized_email = _normalize_email(str(update_fields["email"]))
        existing = get_user_by_email(normalized_email)
        if existing is not None and existing["id"] != user_id:
            raise EmailAlreadyExistsError(
                f"Email already registered: {normalized_email}"
            )
        update_fields["email"] = normalized_email

    user = update_user_record(user_id, update_fields)
    if user is None:
        raise UserNotFoundError(f"User not found: {user_id}")
    return user


def delete_user(user_id: int) -> None:
    if not delete_user_record(user_id):
        raise UserNotFoundError(f"User not found: {user_id}")
