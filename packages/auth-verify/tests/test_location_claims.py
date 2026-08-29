"""Tests for location-scoped JWT claim helpers."""

from __future__ import annotations

import pytest
from brasaland_auth_verify import TokenError, verify_token
from brasaland_auth_verify.location_claims import (
    assert_active_location_authorized,
    get_active_location_slug,
    get_authorized_location_slugs,
    is_all_locations_admin,
    require_active_location_slug,
)
from brasaland_auth_verify.testing import mint_access_token

from tests.conftest import PRIVATE_PEM


def test_admin_claims_return_none_for_authorized_set() -> None:
    token = mint_access_token(
        PRIVATE_PEM,
        is_admin=True,
        extra_claims={
            "location_slug": "miami_brickell",
            "authorized_locations": [],
        },
    )
    claims = verify_token(token)
    assert is_all_locations_admin(claims)
    assert get_authorized_location_slugs(claims) is None
    assert assert_active_location_authorized(claims) == "miami_brickell"


def test_scoped_user_authorized_locations() -> None:
    token = mint_access_token(
        PRIVATE_PEM,
        extra_claims={
            "authorized_locations": ["medellin_centro", "bogota_chapinero"],
            "location_slug": "medellin_centro",
        },
    )
    claims = verify_token(token)
    assert not is_all_locations_admin(claims)
    assert get_authorized_location_slugs(claims) == frozenset(
        {"medellin_centro", "bogota_chapinero"}
    )
    assert get_active_location_slug(claims) == "medellin_centro"
    assert assert_active_location_authorized(claims) == "medellin_centro"


def test_tampered_location_slug_outside_authorized_raises() -> None:
    token = mint_access_token(
        PRIVATE_PEM,
        extra_claims={
            "authorized_locations": ["medellin_centro"],
            "location_slug": "bogota_chapinero",
        },
    )
    claims = verify_token(token)
    with pytest.raises(TokenError, match="not in authorized_locations"):
        assert_active_location_authorized(claims)


def test_missing_location_slug_raises() -> None:
    token = mint_access_token(PRIVATE_PEM)
    claims = verify_token(token)
    assert get_active_location_slug(claims) is None
    with pytest.raises(TokenError, match="Missing location_slug"):
        require_active_location_slug(claims)


def test_scoped_user_empty_authorized_set() -> None:
    token = mint_access_token(
        PRIVATE_PEM,
        extra_claims={
            "authorized_locations": [],
            "location_slug": "medellin_centro",
        },
    )
    claims = verify_token(token)
    assert get_authorized_location_slugs(claims) == frozenset()
    with pytest.raises(TokenError, match="not in authorized_locations"):
        assert_active_location_authorized(claims)
