from __future__ import annotations

from typing import Annotated, Any

from brasaland_auth_verify.deps import get_verified_claims
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from pipelines.rfp_intake.models import Ticket

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

TICKET_ACCESS_DENIED = "Not allowed to access this ticket"


def get_current_user_uuid(
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> str:
    user_id = claims.get("user_id", claims.get("sub"))
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(user_id)


def require_ticket_access(
    ticket: Ticket,
    claims: dict[str, Any],
) -> None:
    """Allow owner or admin; NULL owner denies non-admin (legacy rows)."""
    if bool(claims.get("is_admin")):
        return
    user_id = claims.get("user_id", claims.get("sub"))
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    owner = ticket.owner_user_uuid
    if owner is None or str(owner) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=TICKET_ACCESS_DENIED,
        )
