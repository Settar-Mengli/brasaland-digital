from __future__ import annotations

import os
from typing import Annotated, Any

from brasaland_auth_verify.deps import (
    get_current_user_uuid,
    get_verified_claims,
    require_admin,
)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

WEBSITE_KNOWLEDGE_SVC_CLAIM_ENV = "WEBSITE_KNOWLEDGE_SVC_CLAIM"
DEFAULT_WEBSITE_KNOWLEDGE_SVC_CLAIM = "website-knowledge"


def require_website_service(
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> dict[str, Any]:
    """Require a Bearer token issued for the website guest-chat BFF service."""
    expected = os.environ.get(
        WEBSITE_KNOWLEDGE_SVC_CLAIM_ENV, DEFAULT_WEBSITE_KNOWLEDGE_SVC_CLAIM
    ).strip()
    if claims.get("svc") != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return claims


__all__ = [
    "DEFAULT_WEBSITE_KNOWLEDGE_SVC_CLAIM",
    "get_current_user_uuid",
    "get_verified_claims",
    "oauth2_scheme",
    "require_admin",
    "require_website_service",
]
