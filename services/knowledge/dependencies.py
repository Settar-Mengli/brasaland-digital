from __future__ import annotations

from brasaland_auth_verify.deps import (
    get_current_user_uuid,
    get_verified_claims,
    require_admin,
)
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

__all__ = [
    "get_current_user_uuid",
    "get_verified_claims",
    "oauth2_scheme",
    "require_admin",
]
