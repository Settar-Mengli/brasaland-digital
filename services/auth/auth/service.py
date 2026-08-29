from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from auth.locations import (
    normalize_authorized_locations,
    sorted_canonical_slugs,
    validate_location_slug,
)
from auth.refresh_repository import (
    create_refresh_token as create_refresh_token_record,
    get_by_hash as get_refresh_token_by_hash,
    revoke as revoke_refresh_token_record,
    revoke_all_for_user,
)
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
    InvalidRefreshTokenError,
    InvalidResetTokenError,
    LocationNotAuthorizedError,
    NoLocationAssignedError,
    UserNotFoundError,
    UserRecord,
)

PASSWORD_RESET_TOKEN_TYPE = "password_reset"
REFRESH_TOKEN_TYPE = "refresh"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _reset_token_expire_minutes() -> int:
    return int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", "30"))


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _refresh_token_expire_minutes() -> int:
    return int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))


def self_registration_enabled() -> bool:
    raw = os.environ.get("AUTH_ALLOW_SELF_REGISTER", "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _refresh_token_expired(expires_at: str) -> bool:
    expire_dt = datetime.fromisoformat(expires_at)
    if expire_dt.tzinfo is None:
        expire_dt = expire_dt.replace(tzinfo=timezone.utc)
    return expire_dt <= datetime.now(timezone.utc)


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
    revoke_all_for_user(user_id)


def register_user(
    email: str,
    password: str,
    is_admin: bool = False,
    name: str = "",
    phone: str = "",
    address: str = "",
    authorized_locations: list[str] | None = None,
) -> UserRecord:
    normalized_email = _normalize_email(email)
    if get_user_by_email(normalized_email) is not None:
        raise EmailAlreadyExistsError(
            f"Email already registered: {normalized_email}"
        )

    locations: list[str] = []
    if authorized_locations is not None:
        locations = normalize_authorized_locations(authorized_locations)

    return create_user(
        {
            "email": normalized_email,
            "hashed_password": hash_password(password),
            "is_active": True,
            "is_admin": is_admin,
            "created_at": _utc_now_iso(),
            "name": name,
            "phone": phone,
            "address": address,
            "authorized_locations": locations,
        }
    )


def ensure_bootstrap_admin() -> UserRecord | None:
    """Seed a first admin from env, only when the user store is empty."""
    email = os.environ.get("AUTH_BOOTSTRAP_ADMIN_EMAIL", "").strip()
    password = os.environ.get("AUTH_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email or not password:
        return None
    if list_users():
        return None
    return register_user(email, password, is_admin=True)


def authenticate_user(email: str, password: str) -> UserRecord | None:
    user = get_user_by_email(_normalize_email(email))
    if user is None:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def user_authorized_locations(user: UserRecord) -> list[str]:
    """Return the user's stored authorized location slugs (normalized to [])."""
    return list(user.get("authorized_locations") or [])


def get_effective_authorized_locations(user: UserRecord) -> list[str] | None:
    """Return assigned slugs for scoped users, or None when admin (all locations)."""
    if user["is_admin"]:
        return None
    return user_authorized_locations(user)


def resolve_login_locations(user: UserRecord) -> list[str]:
    """Slugs the user may pick at login (all canonical for admin)."""
    if user["is_admin"]:
        return sorted_canonical_slugs()
    return user_authorized_locations(user)


def validate_login_location(user: UserRecord, location_slug: str) -> str:
    """Validate and normalize the login location slug for this user."""
    normalized = validate_location_slug(location_slug)
    if user["is_admin"]:
        return normalized

    authorized = user_authorized_locations(user)
    if not authorized:
        raise NoLocationAssignedError("No location assigned to this user")
    if normalized not in authorized:
        raise LocationNotAuthorizedError(
            f"Location not authorized for this user: {normalized}"
        )
    return normalized


def issue_access_token(user: UserRecord, location_slug: str | None = None) -> str:
    claims: dict[str, Any] = {
        "sub": str(user["id"]),
        "user_id": user["id"],
        "is_admin": bool(user["is_admin"]),
    }
    if location_slug is not None:
        normalized = validate_login_location(user, location_slug)
        claims["location_slug"] = normalized
        if user["is_admin"]:
            claims["authorized_locations"] = []
        else:
            claims["authorized_locations"] = user_authorized_locations(user)
    return create_access_token(claims)


def issue_refresh_token(
    user: UserRecord,
    location_slug: str | None = None,
    expires_minutes: int | None = None,
) -> str:
    minutes = _refresh_token_expire_minutes() if expires_minutes is None else expires_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {
        "sub": str(user["id"]),
        "user_id": user["id"],
        "type": REFRESH_TOKEN_TYPE,
        "jti": secrets.token_urlsafe(16),
    }
    if location_slug is not None:
        payload["location_slug"] = validate_login_location(user, location_slug)
    token = create_access_token(payload, expires_minutes=minutes)
    create_refresh_token_record(
        {
            "user_id": user["id"],
            "token_hash": _hash_token(token),
            "expires_at": expire_at.isoformat(),
            "revoked": False,
            "created_at": _utc_now_iso(),
        },
    )
    return token


def issue_token_pair(
    user: UserRecord,
    location_slug: str | None = None,
) -> tuple[str, str]:
    return issue_access_token(user, location_slug), issue_refresh_token(
        user, location_slug
    )


def rotate_refresh_token(token: str) -> tuple[str, str]:
    try:
        payload = decode_access_token(token)
    except TokenError as error:
        raise InvalidRefreshTokenError("Invalid or expired refresh token") from error

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    stored = get_refresh_token_by_hash(_hash_token(token))
    if stored is None:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")
    if stored.get("revoked"):
        raise InvalidRefreshTokenError("Invalid or expired refresh token")
    if _refresh_token_expired(stored["expires_at"]):
        raise InvalidRefreshTokenError("Invalid or expired refresh token")
    if not hmac.compare_digest(_hash_token(token), stored["token_hash"]):
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    user_id = _user_id_from_token_payload(payload)
    if user_id is None:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    user = get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        raise InvalidRefreshTokenError("Invalid or expired refresh token")

    location_slug = payload.get("location_slug")
    if location_slug is not None:
        try:
            validate_login_location(user, str(location_slug))
        except (NoLocationAssignedError, LocationNotAuthorizedError) as error:
            raise InvalidRefreshTokenError("Invalid or expired refresh token") from error

    revoke_refresh_token_record(stored["token_hash"])
    return issue_token_pair(user, str(location_slug) if location_slug is not None else None)


def revoke_refresh_token(token: str) -> None:
    try:
        payload = decode_access_token(token)
    except TokenError:
        return

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        return

    stored = get_refresh_token_by_hash(_hash_token(token))
    if stored is None:
        return

    revoke_refresh_token_record(stored["token_hash"])


def can_modify_user(requester: UserRecord, target_user_id: int) -> bool:
    return requester["id"] == target_user_id or requester["is_admin"]


def build_update_fields(
    email: str | None,
    password: str | None,
    authorized_locations: list[str] | None = None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if email is not None:
        fields["email"] = str(email)
    if password is not None:
        fields["hashed_password"] = hash_password(password)
    if authorized_locations is not None:
        fields["authorized_locations"] = normalize_authorized_locations(
            authorized_locations
        )
    return fields


def resolve_active_user(token: str) -> UserRecord | None:
    try:
        payload = decode_access_token(token)
    except TokenError:
        return None

    if payload.get("type") is not None:
        return None

    user_id = _user_id_from_token_payload(payload)
    if user_id is None:
        return None

    user = get_user_by_id(user_id)
    if user is None:
        return None

    if not user["is_active"]:
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

    if "authorized_locations" in update_fields:
        update_fields["authorized_locations"] = normalize_authorized_locations(
            list(update_fields["authorized_locations"])
        )

    user = update_user_record(user_id, update_fields)
    if user is None:
        raise UserNotFoundError(f"User not found: {user_id}")
    return user


def update_profile(
    user_id: int,
    *,
    name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
) -> UserRecord:
    """Update only profile display fields. Never email, password, or flags."""
    fields: dict[str, Any] = {}
    if name is not None:
        fields["name"] = name
    if phone is not None:
        fields["phone"] = phone
    if address is not None:
        fields["address"] = address

    if not fields:
        return get_user(user_id)

    user = update_user_record(user_id, fields)
    if user is None:
        raise UserNotFoundError(f"User not found: {user_id}")
    return user


def delete_user(user_id: int) -> None:
    if not delete_user_record(user_id):
        raise UserNotFoundError(f"User not found: {user_id}")
