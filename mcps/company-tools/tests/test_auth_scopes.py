"""Auth + scope mapping unit tests."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from mcpauth.exceptions import MCPAuthTokenVerificationException

from company_tools_mcp.auth import (
    SCOPE_INVENTORY_READ,
    SCOPE_TICKETS_READ,
    SCOPE_TICKETS_WRITE,
    map_scopes_for_user,
    verify_brasaland_access_token,
)
from company_tools_mcp.errors import (
    AUTHZ_SCOPE_DENIED,
    INVENTORY_WRITE_FORBIDDEN,
)
from company_tools_mcp.scopes import require_scopes
from company_tools_mcp.tools.inventory import create_ingredient_impl
from tests.conftest import make_auth_info
from unittest.mock import MagicMock


def test_baseline_scopes_without_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TICKETS_WRITE_ALLOWLIST", "")
    assert map_scopes_for_user("99") == [
        SCOPE_TICKETS_READ,
        SCOPE_INVENTORY_READ,
    ]


def test_allowlist_grants_tickets_write(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TICKETS_WRITE_ALLOWLIST", "7, 42")
    scopes = map_scopes_for_user("7")
    assert SCOPE_TICKETS_WRITE in scopes
    assert SCOPE_INVENTORY_READ in scopes
    assert "inventory:write" not in scopes


def test_verify_rejects_typed_token() -> None:
    with patch(
        "company_tools_mcp.auth.verify_token",
        return_value={"sub": "1", "user_id": 1, "type": "refresh"},
    ):
        with pytest.raises(MCPAuthTokenVerificationException):
            verify_brasaland_access_token("refresh.jwt")


def test_verify_injects_baseline_scopes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TICKETS_WRITE_ALLOWLIST", "")
    with patch(
        "company_tools_mcp.auth.verify_token",
        return_value={"sub": "5", "user_id": 5},
    ):
        info = verify_brasaland_access_token("access.jwt")
    assert info.subject == "5"
    assert info.scopes == [SCOPE_TICKETS_READ, SCOPE_INVENTORY_READ]


def test_require_scopes_denies_missing() -> None:
    auth = MagicMock()
    auth.auth_info = make_auth_info(scopes=[SCOPE_TICKETS_READ])
    denied = require_scopes(auth, [SCOPE_TICKETS_WRITE])
    assert denied is not None
    assert denied["code"] == AUTHZ_SCOPE_DENIED


def test_create_ingredient_returns_forbidden_not_authz() -> None:
    auth = MagicMock()
    auth.auth_info = make_auth_info()
    result = create_ingredient_impl(auth, name="x", sku="y")
    assert result["code"] == INVENTORY_WRITE_FORBIDDEN
    assert result["ok"] is False
