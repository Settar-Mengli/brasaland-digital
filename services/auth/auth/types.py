from __future__ import annotations

from typing import NotRequired, TypedDict


class UserRecord(TypedDict):
    id: int
    email: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: str
    reset_token_hash: str | None
    reset_token_expires: str | None
    name: NotRequired[str]
    phone: NotRequired[str]
    address: NotRequired[str]
    authorized_locations: NotRequired[list[str]]


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already stored."""


class UserNotFoundError(Exception):
    """Raised when a user id does not exist."""


class InvalidResetTokenError(Exception):
    """Raised when a password-reset token is invalid, expired, or already used."""


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is invalid, expired, or revoked."""


class NoLocationAssignedError(Exception):
    """Raised when a scoped user has no authorized locations or none were chosen."""


class LocationNotAuthorizedError(Exception):
    """Raised when the requested location is outside the user's assignment."""
