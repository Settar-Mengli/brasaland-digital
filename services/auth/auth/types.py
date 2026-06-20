from __future__ import annotations

from typing import TypedDict


class UserRecord(TypedDict):
    id: int
    email: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: str
    reset_token_hash: str | None
    reset_token_expires: str | None


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already stored."""


class UserNotFoundError(Exception):
    """Raised when a user id does not exist."""


class InvalidResetTokenError(Exception):
    """Raised when a password-reset token is invalid, expired, or already used."""
