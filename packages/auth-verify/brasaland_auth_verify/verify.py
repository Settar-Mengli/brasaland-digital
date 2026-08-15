from __future__ import annotations

import os

from jose import JWTError, jwt


class TokenError(Exception):
    """Raised when a JWT cannot be decoded or validated."""


def _require_public_key() -> str:
    key = os.environ.get("JWT_PUBLIC_KEY")
    if not key:
        raise ValueError("JWT_PUBLIC_KEY environment variable is required")
    return key


def ensure_jwt_configured() -> None:
    """Fail fast at process start when the verify key is missing."""
    _require_public_key()


def _algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "RS256")


def verify_token(token: str) -> dict:
    """Decode and validate an RS256 JWT with the public key; return claims."""
    try:
        return jwt.decode(
            token,
            _require_public_key(),
            algorithms=[_algorithm()],
        )
    except JWTError as error:
        raise TokenError("Invalid or expired access token") from error
