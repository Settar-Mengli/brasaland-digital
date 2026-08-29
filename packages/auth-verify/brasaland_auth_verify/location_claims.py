"""Helpers for location-scoped JWT claims (verify-only)."""

from __future__ import annotations

from typing import Any

from .verify import TokenError


def is_all_locations_admin(claims: dict[str, Any]) -> bool:
    """Return True when the token carries the all-locations admin bypass."""
    return bool(claims.get("is_admin"))


def get_authorized_location_slugs(claims: dict[str, Any]) -> frozenset[str] | None:
    """Return assigned slugs from the token, or None when admin (all locations)."""
    if is_all_locations_admin(claims):
        return None
    raw = claims.get("authorized_locations")
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(str(slug) for slug in raw)


def get_active_location_slug(claims: dict[str, Any]) -> str | None:
    """Return the active location slug claim when present."""
    raw = claims.get("location_slug")
    if raw is None:
        return None
    return str(raw)


def require_active_location_slug(claims: dict[str, Any]) -> str:
    """Return location_slug or raise TokenError when missing."""
    slug = get_active_location_slug(claims)
    if slug is None:
        raise TokenError("Missing location_slug claim")
    return slug


def assert_active_location_authorized(claims: dict[str, Any]) -> str:
    """Return location_slug when authorized per the signed claims snapshot."""
    slug = require_active_location_slug(claims)
    if is_all_locations_admin(claims):
        return slug

    authorized = get_authorized_location_slugs(claims)
    if authorized is None:
        return slug
    if slug not in authorized:
        raise TokenError("location_slug is not in authorized_locations")
    return slug
