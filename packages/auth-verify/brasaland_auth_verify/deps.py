"""FastAPI dependencies for Brasaland services (verify-only, RS256).

Import from ``brasaland_auth_verify.deps`` so that non-FastAPI consumers of
this package never import FastAPI.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .verify import TokenError, verify_token

_bearer_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verified_claims(token: str) -> dict[str, Any]:
    try:
        claims = verify_token(token)
    except TokenError as error:
        raise _unauthorized("Could not validate credentials") from error
    # Access tokens omit ``type``; refresh/reset tokens carry it.
    if claims.get("type") is not None:
        raise _unauthorized("Could not validate credentials")
    return claims


def _identity(claims: dict[str, Any]) -> str:
    user_id = claims.get("user_id", claims.get("sub"))
    if user_id is None:
        raise _unauthorized("Could not validate credentials")
    return str(user_id)


def get_verified_claims(
    token: Annotated[str | None, Depends(_bearer_scheme)],
) -> dict[str, Any]:
    """Require a valid access token; return its claims."""
    if token is None:
        raise _unauthorized("Not authenticated")
    return _verified_claims(token)


def get_current_user_uuid(
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> str:
    """Require a valid access token; return the caller identity as a string."""
    return _identity(claims)


def get_optional_user_uuid(
    token: Annotated[str | None, Depends(_bearer_scheme)],
) -> str | None:
    """Return the caller identity when a token is presented, else ``None``.

    A missing token yields ``None``; a present-but-invalid token is rejected
    with 401 rather than silently treated as anonymous.
    """
    if token is None:
        return None
    return _identity(_verified_claims(token))


def require_admin(
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> str:
    """Require a valid access token whose ``is_admin`` claim is true."""
    if not claims.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return _identity(claims)
