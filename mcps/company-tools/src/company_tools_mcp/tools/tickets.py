"""Incident/ticket MCP tools — one responsibility each."""

from __future__ import annotations

from typing import Any

from brasaland_shared.constants import (
    REQUIRED_FIELDS,
    VALID_BRANCHES,
    VALID_CATEGORIES,
    VALID_ORIGINS,
    VALID_STATUSES,
)
from mcpauth import MCPAuth

from company_tools_mcp.auth import SCOPE_TICKETS_READ, SCOPE_TICKETS_WRITE
from company_tools_mcp.clients import incidents as incidents_client
from company_tools_mcp.errors import (
    NOT_FOUND,
    UPSTREAM_ERROR,
    VALIDATION_ERROR,
    error_payload,
    ok_payload,
)
from company_tools_mcp.logging_util import log_invocation
from company_tools_mcp.scopes import current_user_id, require_scopes


def _is_numeric_ref(ticket_ref: str) -> bool:
    return ticket_ref.isdigit()


def _match_source_incident_id(needle: str) -> dict[str, Any]:
    status, rows = incidents_client.list_incidents()
    if status != 200 or not isinstance(rows, list):
        return error_payload(
            UPSTREAM_ERROR,
            f"incident-manager list HTTP {status}",
        )
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("source_incident_id")) == needle
    ]
    if not matches:
        return error_payload(NOT_FOUND, "ticket not found")
    return ok_payload(incident=matches[0], matched_by="source_incident_id")


def check_ticket_status_impl(mcp_auth: MCPAuth, ticket_ref: str) -> dict[str, Any]:
    denied = require_scopes(mcp_auth, [SCOPE_TICKETS_READ])
    user_id = current_user_id(mcp_auth)
    if denied:
        log_invocation(
            tool="check_ticket_status",
            client_user_id=user_id,
            result=denied["code"],
        )
        return denied

    ref = (ticket_ref or "").strip()
    if not ref:
        result = error_payload(VALIDATION_ERROR, "ticket_ref is required")
        log_invocation(
            tool="check_ticket_status",
            client_user_id=user_id,
            result=result["code"],
        )
        return result

    try:
        if not _is_numeric_ref(ref):
            result = _match_source_incident_id(ref)
        else:
            status, payload = incidents_client.get_incident_by_id(int(ref))
            if status == 200 and isinstance(payload, dict):
                result = ok_payload(incident=payload, matched_by="id")
            elif status == 404:
                result = _match_source_incident_id(ref)
            else:
                result = error_payload(
                    UPSTREAM_ERROR,
                    f"incident-manager HTTP {status}",
                )
    except Exception as exc:  # noqa: BLE001
        result = error_payload(UPSTREAM_ERROR, str(exc))

    log_invocation(
        tool="check_ticket_status",
        client_user_id=user_id,
        result="ok" if result.get("ok") else result.get("code", "error"),
    )
    return result


def create_ticket_impl(
    mcp_auth: MCPAuth,
    *,
    title: str,
    description: str,
    category: str,
    status: str,
    origin: str,
    branch: str,
) -> dict[str, Any]:
    denied = require_scopes(mcp_auth, [SCOPE_TICKETS_WRITE])
    user_id = current_user_id(mcp_auth)
    if denied:
        log_invocation(
            tool="create_ticket",
            client_user_id=user_id,
            result=denied["code"],
        )
        return denied

    body = {
        "title": title,
        "description": description,
        "category": category,
        "status": status,
        "origin": origin,
        "branch": branch,
    }
    # Soft gap B: require all CONTEXT REQUIRED_FIELDS — do not rely on API default.
    missing = [field for field in REQUIRED_FIELDS if not str(body.get(field) or "").strip()]
    if missing:
        result = error_payload(
            VALIDATION_ERROR,
            f"Missing required fields: {', '.join(missing)}",
            fields=missing,
        )
        log_invocation(
            tool="create_ticket", client_user_id=user_id, result=result["code"]
        )
        return result

    if category not in VALID_CATEGORIES:
        result = error_payload(VALIDATION_ERROR, f"Invalid category: {category}")
    elif status not in VALID_STATUSES:
        result = error_payload(VALIDATION_ERROR, f"Invalid status: {status}")
    elif origin not in VALID_ORIGINS:
        result = error_payload(VALIDATION_ERROR, f"Invalid origin: {origin}")
    elif branch not in VALID_BRANCHES:
        result = error_payload(VALIDATION_ERROR, f"Invalid branch: {branch}")
    else:
        result = None

    if result is not None:
        log_invocation(
            tool="create_ticket", client_user_id=user_id, result=result["code"]
        )
        return result

    try:
        http_status, payload = incidents_client.create_incident(body)
    except Exception as exc:  # noqa: BLE001
        result = error_payload(UPSTREAM_ERROR, str(exc))
        log_invocation(
            tool="create_ticket", client_user_id=user_id, result=result["code"]
        )
        return result

    if http_status in (200, 201) and isinstance(payload, dict):
        result = ok_payload(incident=payload)
    elif http_status == 400:
        result = error_payload(
            VALIDATION_ERROR,
            "incident-manager rejected create",
            detail=payload,
        )
    else:
        result = error_payload(
            UPSTREAM_ERROR,
            f"incident-manager HTTP {http_status}",
            detail=payload,
        )
    log_invocation(
        tool="create_ticket",
        client_user_id=user_id,
        result="ok" if result.get("ok") else result.get("code", "error"),
    )
    return result


def update_ticket_status_impl(
    mcp_auth: MCPAuth, *, incident_id: int, status: str
) -> dict[str, Any]:
    denied = require_scopes(mcp_auth, [SCOPE_TICKETS_WRITE])
    user_id = current_user_id(mcp_auth)
    if denied:
        log_invocation(
            tool="update_ticket_status",
            client_user_id=user_id,
            result=denied["code"],
        )
        return denied

    if status not in VALID_STATUSES:
        result = error_payload(VALIDATION_ERROR, f"Invalid status: {status}")
        log_invocation(
            tool="update_ticket_status",
            client_user_id=user_id,
            result=result["code"],
        )
        return result

    try:
        # Soft gap A noted: upstream is unauthenticated; only PATCH .../status.
        http_status, payload = incidents_client.patch_incident_status(
            incident_id, status
        )
    except Exception as exc:  # noqa: BLE001
        result = error_payload(UPSTREAM_ERROR, str(exc))
        log_invocation(
            tool="update_ticket_status",
            client_user_id=user_id,
            result=result["code"],
        )
        return result

    if http_status == 200 and isinstance(payload, dict):
        result = ok_payload(incident=payload)
    elif http_status == 404:
        result = error_payload(NOT_FOUND, "Incident not found")
    elif http_status == 400:
        result = error_payload(
            VALIDATION_ERROR,
            "invalid status transition",
            detail=payload,
        )
    else:
        result = error_payload(
            UPSTREAM_ERROR,
            f"incident-manager HTTP {http_status}",
            detail=payload,
        )
    log_invocation(
        tool="update_ticket_status",
        client_user_id=user_id,
        result="ok" if result.get("ok") else result.get("code", "error"),
    )
    return result
