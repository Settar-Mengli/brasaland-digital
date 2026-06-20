from __future__ import annotations

from typing import TypedDict


class UserRecord(TypedDict):
    id: int
    email: str
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: str


class EmailAlreadyExistsError(Exception):
    """Raised when registering an email that is already stored."""


class UserNotFoundError(Exception):
    """Raised when a user id does not exist."""
