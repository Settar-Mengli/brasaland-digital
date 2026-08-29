"""Shared helpers for auth service tests."""

from __future__ import annotations

TEST_LOCATION_SLUG = "medellin_centro"


def login_form(
    username: str,
    password: str,
    location_slug: str = TEST_LOCATION_SLUG,
) -> dict[str, str]:
    return {
        "username": username,
        "password": password,
        "location_slug": location_slug,
    }


def assign_test_location(email: str) -> None:
    from auth.repository import get_user_by_email
    from auth.service import update_user

    user = get_user_by_email(email.strip().lower())
    if user is None:
        raise RuntimeError(f"user not found: {email}")
    update_user(user["id"], {"authorized_locations": [TEST_LOCATION_SLUG]})
