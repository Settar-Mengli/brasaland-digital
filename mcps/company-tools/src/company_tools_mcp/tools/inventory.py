"""Inventory MCP tools — read stock; writes explicitly rejected."""

from __future__ import annotations

from typing import Any

from mcpauth import MCPAuth

from company_tools_mcp.auth import SCOPE_INVENTORY_READ
from company_tools_mcp.clients import inventory as inventory_client
from company_tools_mcp.errors import (
    INVENTORY_WRITE_FORBIDDEN,
    INVENTORY_WRITE_MESSAGE,
    NOT_FOUND,
    UPSTREAM_ERROR,
    VALIDATION_ERROR,
    error_payload,
    ok_payload,
)
from company_tools_mcp.logging_util import log_invocation
from company_tools_mcp.scopes import current_user_id, require_scopes


def check_stock_impl(
    mcp_auth: MCPAuth,
    *,
    ingredient_id: int | None = None,
    sku: str | None = None,
) -> dict[str, Any]:
    denied = require_scopes(mcp_auth, [SCOPE_INVENTORY_READ])
    user_id = current_user_id(mcp_auth)
    if denied:
        log_invocation(
            tool="check_stock", client_user_id=user_id, result=denied["code"]
        )
        return denied

    if ingredient_id is None and not (sku and str(sku).strip()):
        result = error_payload(
            VALIDATION_ERROR,
            "ingredient_id or sku is required",
        )
        log_invocation(
            tool="check_stock", client_user_id=user_id, result=result["code"]
        )
        return result

    try:
        if ingredient_id is not None:
            status, payload = inventory_client.get_product(ingredient_id)
            if status == 200 and isinstance(payload, dict):
                result = ok_payload(ingredient=payload)
            elif status == 404:
                result = error_payload(NOT_FOUND, "ingredient not found")
            else:
                result = error_payload(
                    UPSTREAM_ERROR, f"inventory HTTP {status}"
                )
        else:
            status, rows = inventory_client.list_products()
            if status != 200 or not isinstance(rows, list):
                result = error_payload(
                    UPSTREAM_ERROR, f"inventory HTTP {status}"
                )
            else:
                needle = str(sku).strip()
                matches = [
                    row
                    for row in rows
                    if isinstance(row, dict) and str(row.get("sku")) == needle
                ]
                if not matches:
                    result = error_payload(NOT_FOUND, "ingredient not found")
                else:
                    result = ok_payload(ingredient=matches[0])
    except Exception as exc:  # noqa: BLE001
        result = error_payload(UPSTREAM_ERROR, str(exc))

    log_invocation(
        tool="check_stock",
        client_user_id=user_id,
        result="ok" if result.get("ok") else result.get("code", "error"),
    )
    return result


def _reject_write(mcp_auth: MCPAuth, tool: str) -> dict[str, Any]:
    denied = require_scopes(mcp_auth, [SCOPE_INVENTORY_READ])
    user_id = current_user_id(mcp_auth)
    if denied:
        log_invocation(tool=tool, client_user_id=user_id, result=denied["code"])
        return denied
    result = error_payload(INVENTORY_WRITE_FORBIDDEN, INVENTORY_WRITE_MESSAGE)
    log_invocation(tool=tool, client_user_id=user_id, result=result["code"])
    return result


def create_ingredient_impl(mcp_auth: MCPAuth, **_kwargs: Any) -> dict[str, Any]:
    return _reject_write(mcp_auth, "create_ingredient")


def record_inbound_impl(mcp_auth: MCPAuth, **_kwargs: Any) -> dict[str, Any]:
    return _reject_write(mcp_auth, "record_inbound")


def record_outbound_impl(mcp_auth: MCPAuth, **_kwargs: Any) -> dict[str, Any]:
    return _reject_write(mcp_auth, "record_outbound")
