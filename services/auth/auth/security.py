from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Raised when a JWT cannot be decoded or validated."""


def _require_jwt_private_key() -> str:
    key = os.environ.get("JWT_PRIVATE_KEY")
    if not key:
        raise ValueError("JWT_PRIVATE_KEY environment variable is required")
    return key


def _require_jwt_public_key() -> str:
    key = os.environ.get("JWT_PUBLIC_KEY")
    if not key:
        raise ValueError("JWT_PUBLIC_KEY environment variable is required")
    return key


def _jwt_algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "RS256")


def _default_expire_minutes() -> int:
    raw = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    return int(raw)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    payload = data.copy()
    minutes = _default_expire_minutes() if expires_minutes is None else expires_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload["exp"] = int(expire_at.timestamp())
    return jwt.encode(payload, _require_jwt_private_key(), algorithm=_jwt_algorithm())


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            _require_jwt_public_key(),
            algorithms=[_jwt_algorithm()],
        )
    except JWTError as error:
        raise TokenError("Invalid or expired access token") from error
