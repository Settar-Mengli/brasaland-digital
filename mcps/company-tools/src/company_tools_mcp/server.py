"""Brasaland company-tools MCP server (Streamable HTTP + mcpauth).

Does NOT use FastMCP built-in auth. Bearer validation and scope injection go
through mcpauth with a custom verify over brasaland_auth_verify.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastmcp import FastMCP
from mcpauth import MCPAuth
from mcpauth.exceptions import (
    BearerAuthExceptionCode,
    MCPAuthBearerAuthException,
    MCPAuthTokenVerificationException,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from company_tools_mcp.auth import (
    GRANTABLE_SCOPES,
    auth_issuer_url,
    build_auth_server_config,
    make_verify_fn,
    mcp_resource_url,
)
from company_tools_mcp.errors import (
    AUTH_INVALID,
    AUTH_REQUIRED,
    AUTHZ_SCOPE_DENIED,
)
from company_tools_mcp.tools import inventory as inventory_tools
from company_tools_mcp.tools import tickets as ticket_tools

logger = logging.getLogger("company_tools_mcp")

mcp_auth = MCPAuth(server=build_auth_server_config())
mcp = FastMCP(
    name="Brasaland Company Tools",
    instructions=(
        "OAuth-protected MCP tools for Brasaland incidents and read-only inventory. "
        "Present a Brasaland RS256 access Bearer token. Scopes are mapped at this "
        "resource server (not embedded in the JWT)."
    ),
)


def _remap_auth_error(body: dict[str, Any], status_code: int) -> tuple[int, dict[str, Any]]:
    """Map mcpauth error codes to AUTH_REQUIRED / AUTH_INVALID / AUTHZ_SCOPE_DENIED."""
    raw = str(body.get("error") or "")
    if raw in {
        BearerAuthExceptionCode.MISSING_AUTH_HEADER.value,
        BearerAuthExceptionCode.INVALID_AUTH_HEADER_FORMAT.value,
        BearerAuthExceptionCode.MISSING_BEARER_TOKEN.value,
    }:
        return 401, {
            "code": AUTH_REQUIRED,
            "message": body.get("error_description") or "Bearer token required",
            "error": raw,
        }
    if raw == BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES.value:
        return 403, {
            "code": AUTHZ_SCOPE_DENIED,
            "message": body.get("error_description") or "Missing required scopes",
            "error": raw,
        }
    return 401, {
        "code": AUTH_INVALID,
        "message": body.get("error_description") or "Invalid or expired access token",
        "error": raw or "invalid_token",
    }


class RemapAuthErrorMiddleware:
    """ASGI wrapper: rewrite mcpauth JSON errors to distinct Brasaland codes."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_holder: dict[str, int] = {}
        headers_holder: dict[str, list[tuple[bytes, bytes]]] = {"value": []}
        body_chunks: list[bytes] = []

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = int(message["status"])
                headers_holder["value"] = list(message.get("headers") or [])
                return
            if message["type"] == "http.response.body":
                body_chunks.append(message.get("body") or b"")
                if message.get("more_body"):
                    return
                raw = b"".join(body_chunks)
                status = status_holder.get("code", 200)
                if status in (401, 403):
                    try:
                        parsed = json.loads(raw.decode("utf-8") or "{}")
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        parsed = {"error": "invalid_token", "error_description": raw.decode("utf-8", errors="replace")}
                    if isinstance(parsed, dict) and (
                        "error" in parsed or "code" not in parsed
                    ):
                        new_status, new_body = _remap_auth_error(parsed, status)
                        payload = json.dumps(new_body).encode("utf-8")
                        headers = [
                            (k, v)
                            for k, v in headers_holder["value"]
                            if k.lower() != b"content-length"
                        ]
                        headers.append(
                            (b"content-length", str(len(payload)).encode("ascii"))
                        )
                        await send(
                            {
                                "type": "http.response.start",
                                "status": new_status,
                                "headers": headers,
                            }
                        )
                        await send(
                            {
                                "type": "http.response.body",
                                "body": payload,
                                "more_body": False,
                            }
                        )
                        return
                await send(
                    {
                        "type": "http.response.start",
                        "status": status,
                        "headers": headers_holder["value"],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": raw,
                        "more_body": False,
                    }
                )
                return
            await send(message)

        await self.app(scope, receive, send_wrapper)


async def protected_resource_metadata(_request: Request) -> Response:
    """RFC 9728 Protected Resource Metadata (mcpauth AS metadata is separate)."""
    resource = mcp_resource_url()
    return JSONResponse(
        {
            "resource": resource,
            "authorization_servers": [auth_issuer_url()],
            "scopes_supported": list(GRANTABLE_SCOPES),
            "bearer_methods_supported": ["header"],
        }
    )


@mcp.tool(
    name="check_ticket_status",
    description=(
        "Look up a Brasaland incident by numeric id or source_incident_id "
        "(e.g. MANUAL-98). Returns live status fields. Scope: tickets:read."
    ),
)
def check_ticket_status(ticket_ref: str) -> dict[str, Any]:
    return ticket_tools.check_ticket_status_impl(mcp_auth, ticket_ref)


@mcp.tool(
    name="create_ticket",
    description=(
        "Create an incident. Requires ALL of title, description, category, status, "
        "origin, branch with CONTEXT allowed values. Scope: tickets:write."
    ),
)
def create_ticket(
    title: str,
    description: str,
    category: str,
    status: str,
    origin: str,
    branch: str,
) -> dict[str, Any]:
    return ticket_tools.create_ticket_impl(
        mcp_auth,
        title=title,
        description=description,
        category=category,
        status=status,
        origin=origin,
        branch=branch,
    )


@mcp.tool(
    name="update_ticket_status",
    description=(
        "Change incident lifecycle status via PATCH /api/incidents/{id}/status only. "
        "Scope: tickets:write."
    ),
)
def update_ticket_status(incident_id: int, status: str) -> dict[str, Any]:
    return ticket_tools.update_ticket_status_impl(
        mcp_auth, incident_id=incident_id, status=status
    )


@mcp.tool(
    name="check_stock",
    description=(
        "Read-only ingredient stock query by ingredient_id or sku. Returns "
        "current_stock and Ingredient fields. Scope: inventory:read."
    ),
)
def check_stock(
    ingredient_id: int | None = None,
    sku: str | None = None,
) -> dict[str, Any]:
    return inventory_tools.check_stock_impl(
        mcp_auth, ingredient_id=ingredient_id, sku=sku
    )


@mcp.tool(
    name="create_ingredient",
    description=(
        "REJECTED write attempt. Inventory is read-only for MCP clients; always "
        "returns INVENTORY_WRITE_FORBIDDEN. Scope: inventory:read."
    ),
)
def create_ingredient(
    name: str = "",
    sku: str = "",
    unit: str = "",
    category: str = "",
    country: str = "",
) -> dict[str, Any]:
    return inventory_tools.create_ingredient_impl(
        mcp_auth,
        name=name,
        sku=sku,
        unit=unit,
        category=category,
        country=country,
    )


@mcp.tool(
    name="record_inbound",
    description=(
        "REJECTED write attempt for inbound stock. Always returns "
        "INVENTORY_WRITE_FORBIDDEN. Scope: inventory:read."
    ),
)
def record_inbound(
    ingredient_id: int = 0,
    quantity: float = 0.0,
) -> dict[str, Any]:
    return inventory_tools.record_inbound_impl(
        mcp_auth, ingredient_id=ingredient_id, quantity=quantity
    )


@mcp.tool(
    name="record_outbound",
    description=(
        "REJECTED write attempt for outbound stock. Always returns "
        "INVENTORY_WRITE_FORBIDDEN. Scope: inventory:read."
    ),
)
def record_outbound(
    ingredient_id: int = 0,
    quantity: float = 0.0,
    reason: str = "consumption",
) -> dict[str, Any]:
    return inventory_tools.record_outbound_impl(
        mcp_auth,
        ingredient_id=ingredient_id,
        quantity=quantity,
        reason=reason,
    )


class PathScopedBearerMiddleware:
    """Apply mcpauth bearer auth only to MCP tool paths; leave discovery public."""

    def __init__(self, app: ASGIApp, bearer_middleware_cls: type) -> None:
        self.app = app
        self._bearer = bearer_middleware_cls(app)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope.get("path") or ""
            if path == "/mcp" or path.startswith("/mcp/"):
                await self._bearer(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_asgi_app() -> ASGIApp:
    """Build Streamable HTTP app with mcpauth bearer middleware + PRM."""
    bearer_cls = mcp_auth.bearer_auth_middleware(
        make_verify_fn(),
        audience=None,  # our JWTs have no aud claim
        required_scopes=None,  # per-tool scopes enforced inside tools
        show_error_details=True,
    )
    mcp_app = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        stateless_http=True,
    )

    async def prm_handler(request: Request) -> Response:
        return await protected_resource_metadata(request)

    # PRM + AS metadata are public; /mcp requires Bearer.
    routes = [
        Route(
            "/.well-known/oauth-protected-resource",
            prm_handler,
            methods=["GET"],
        ),
        mcp_auth.metadata_route(),
        *mcp_app.routes,
    ]
    inner = Starlette(routes=routes, lifespan=mcp_app.lifespan)
    protected = PathScopedBearerMiddleware(inner, bearer_cls)
    return RemapAuthErrorMiddleware(protected)


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "company_tools_mcp.server:create_asgi_app",
        factory=True,
        host="0.0.0.0",
        port=8016,
    )


# Raise typed mcpauth exceptions from verify so middleware maps them.
_ = (MCPAuthBearerAuthException, MCPAuthTokenVerificationException)
