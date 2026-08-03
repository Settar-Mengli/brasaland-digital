"""Scope helpers for per-tool required_scopes checks."""

from __future__ import annotations

from typing import Any

from mcpauth import MCPAuth

from company_tools_mcp.errors import AUTHZ_SCOPE_DENIED, error_payload


def current_user_id(mcp_auth: MCPAuth) -> str | None:
    info = mcp_auth.auth_info
    if info is None:
        return None
    return info.subject


def require_scopes(
    mcp_auth: MCPAuth, required: list[str]
) -> dict[str, Any] | None:
    """Return an AUTHZ_SCOPE_DENIED payload if scopes are missing; else None."""
    info = mcp_auth.auth_info
    if info is None:
        return error_payload(
            AUTHZ_SCOPE_DENIED,
            "Authenticated identity required",
            missing_scopes=required,
        )
    missing = [scope for scope in required if scope not in info.scopes]
    if missing:
        return error_payload(
            AUTHZ_SCOPE_DENIED,
            f"Missing required scopes: {', '.join(missing)}",
            missing_scopes=missing,
        )
    return None
