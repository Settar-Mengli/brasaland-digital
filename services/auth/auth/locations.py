"""Canonical location slugs for auth assignments and JWT claims.

Must stay in sync with:
- data/pipelines/locations.py LOCATION_DIMENSIONS keys
- uis/backoffice/lib/locations.ts LOCATION_MAP values
"""

from __future__ import annotations

# Underscore slugs — 14 Brasaland locations (CO + US).
CANONICAL_LOCATION_SLUGS: frozenset[str] = frozenset(
    {
        "medellin_centro",
        "medellin_poblado",
        "medellin_laureles",
        "bogota_zona_rosa",
        "bogota_chapinero",
        "bogota_usaquen",
        "bogota_norte",
        "cali_san_fernando",
        "cali_granada",
        "cali_ciudad_jardin",
        "miami_brickell",
        "miami_wynwood",
        "miami_coral_gables",
        "miami_kendall",
    }
)


class InvalidLocationSlugError(ValueError):
    """Raised when a location slug is unknown or not in the user's assignment."""


def validate_location_slug(slug: str) -> str:
    """Normalize and validate a single location slug."""
    normalized = slug.strip()
    if normalized not in CANONICAL_LOCATION_SLUGS:
        raise InvalidLocationSlugError(f"Unknown location slug: {slug}")
    return normalized


def normalize_authorized_locations(slugs: list[str]) -> list[str]:
    """Validate, dedupe, and sort location slugs for stable storage."""
    seen: set[str] = set()
    normalized: list[str] = []
    for slug in slugs:
        valid = validate_location_slug(slug)
        if valid not in seen:
            seen.add(valid)
            normalized.append(valid)
    return sorted(normalized)


def sorted_canonical_slugs() -> list[str]:
    """Return all canonical slugs in stable sorted order."""
    return sorted(CANONICAL_LOCATION_SLUGS)
