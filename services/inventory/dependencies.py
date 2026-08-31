from __future__ import annotations

from typing import Annotated, Any

from brasaland_auth_verify.deps import get_current_user_uuid, get_verified_claims
from brasaland_auth_verify.location_claims import get_authorized_location_slugs
from fastapi import Depends, HTTPException, Query, status

MIN_LOCATION_ID = 1
MAX_LOCATION_ID = 14


# Backend authorization catalog. Keep in sync with auth/auth/locations.py,
# data/pipelines/locations.py, and uis/backoffice/lib/locations.ts.
LOCATION_ID_TO_SLUG: dict[int, str] = {
    1: "medellin_centro",
    2: "medellin_poblado",
    3: "medellin_laureles",
    4: "bogota_zona_rosa",
    5: "bogota_chapinero",
    6: "bogota_usaquen",
    7: "bogota_norte",
    8: "cali_san_fernando",
    9: "cali_granada",
    10: "cali_ciudad_jardin",
    11: "miami_brickell",
    12: "miami_wynwood",
    13: "miami_coral_gables",
    14: "miami_kendall",
}


def assert_authorized_location_id(claims: dict[str, Any], location_id: int) -> int:
    """Require access to the requested numeric inventory location."""
    authorized_slugs = get_authorized_location_slugs(claims)
    requested_slug = LOCATION_ID_TO_SLUG[location_id]
    if authorized_slugs is not None and requested_slug not in authorized_slugs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Location access denied",
        )
    return location_id


def require_authorized_location_id(
    location_id: Annotated[
        int,
        Query(ge=MIN_LOCATION_ID, le=MAX_LOCATION_ID),
    ],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> int:
    """Require access to the requested numeric inventory location (query param)."""
    return assert_authorized_location_id(claims, location_id)


__all__ = [
    "assert_authorized_location_id",
    "get_current_user_uuid",
    "require_authorized_location_id",
]
