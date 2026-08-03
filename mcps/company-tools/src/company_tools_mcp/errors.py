"""Distinct MCP error codes for auth, authz, validation, and inventory policy."""

from __future__ import annotations

from typing import Any


AUTH_REQUIRED = "AUTH_REQUIRED"
AUTH_INVALID = "AUTH_INVALID"
AUTHZ_SCOPE_DENIED = "AUTHZ_SCOPE_DENIED"
VALIDATION_ERROR = "VALIDATION_ERROR"
NOT_FOUND = "NOT_FOUND"
UPSTREAM_ERROR = "UPSTREAM_ERROR"
INVENTORY_WRITE_FORBIDDEN = "INVENTORY_WRITE_FORBIDDEN"

INVENTORY_WRITE_MESSAGE = (
    "Inventory is read-only for MCP clients. "
    "Creating ingredients or recording inbound/outbound orders is forbidden."
)


def error_payload(code: str, message: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message, "ok": False}
    body.update(extra)
    return body


def ok_payload(**fields: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"ok": True}
    body.update(fields)
    return body
