"""Shared fixtures for company-tools MCP tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from mcpauth import AuthInfo

from company_tools_mcp.auth import (
    SCOPE_INVENTORY_READ,
    SCOPE_TICKETS_READ,
    SCOPE_TICKETS_WRITE,
    auth_issuer_url,
)


def make_auth_info(
    *,
    user_id: str = "1",
    scopes: list[str] | None = None,
    token: str = "test-token",
) -> AuthInfo:
    return AuthInfo(
        token=token,
        issuer=auth_issuer_url(),
        client_id=user_id,
        subject=user_id,
        scopes=scopes
        if scopes is not None
        else [SCOPE_TICKETS_READ, SCOPE_INVENTORY_READ],
        claims={"user_id": int(user_id) if user_id.isdigit() else user_id},
    )


@pytest.fixture
def baseline_auth() -> MagicMock:
    auth = MagicMock()
    auth.auth_info = make_auth_info(user_id="42")
    return auth


@pytest.fixture
def writer_auth() -> MagicMock:
    auth = MagicMock()
    auth.auth_info = make_auth_info(
        user_id="7",
        scopes=[SCOPE_TICKETS_READ, SCOPE_TICKETS_WRITE, SCOPE_INVENTORY_READ],
    )
    return auth
