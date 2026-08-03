"""mcpauth custom verify + capability-mapped scopes (injected at the RS).

Scopes are NOT minted by services/auth. After RS256 verification via
brasaland_auth_verify, this layer attaches scopes to AuthInfo.

Rule:
- any valid access token → tickets:read, inventory:read
- user_id in MCP_TICKETS_WRITE_ALLOWLIST → also tickets:write
- inventory:write is never grantable
"""

from __future__ import annotations

import os
from typing import Callable

from brasaland_auth_verify import TokenError, verify_token
from mcpauth import AuthInfo
from mcpauth.config import (
    AuthServerConfig,
    AuthServerType,
    AuthorizationServerMetadata,
)
from mcpauth.exceptions import (
    MCPAuthTokenVerificationException,
    MCPAuthTokenVerificationExceptionCode,
)

SCOPE_TICKETS_READ = "tickets:read"
SCOPE_TICKETS_WRITE = "tickets:write"
SCOPE_INVENTORY_READ = "inventory:read"

BASELINE_SCOPES: tuple[str, ...] = (SCOPE_TICKETS_READ, SCOPE_INVENTORY_READ)
GRANTABLE_SCOPES: tuple[str, ...] = (
    SCOPE_TICKETS_READ,
    SCOPE_TICKETS_WRITE,
    SCOPE_INVENTORY_READ,
)


def auth_issuer_url() -> str:
    return os.environ.get("AUTH_ISSUER_URL", "http://localhost:8002").rstrip("/")


def mcp_resource_url() -> str:
    return os.environ.get(
        "MCP_RESOURCE_URL", "http://localhost:8016/mcp"
    ).rstrip("/")


def tickets_write_allowlist() -> set[str]:
    raw = os.environ.get("MCP_TICKETS_WRITE_ALLOWLIST", "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def map_scopes_for_user(user_id: str) -> list[str]:
    scopes = list(BASELINE_SCOPES)
    if user_id in tickets_write_allowlist():
        scopes.append(SCOPE_TICKETS_WRITE)
    return scopes


def build_auth_server_config() -> AuthServerConfig:
    issuer = auth_issuer_url()
    return AuthServerConfig(
        type=AuthServerType.OAUTH,
        metadata=AuthorizationServerMetadata(
            issuer=issuer,
            authorization_endpoint=f"{issuer}/oauth/authorize",
            token_endpoint=f"{issuer}/oauth/token",
            response_types_supported=["code"],
            code_challenge_methods_supported=["S256"],
            grant_types_supported=["authorization_code"],
            scope_supported=list(GRANTABLE_SCOPES),
        ),
    )


def verify_brasaland_access_token(token: str) -> AuthInfo:
    """Custom mcpauth verify: RS256 + reject typed tokens + inject scopes."""
    try:
        payload = verify_token(token)
    except TokenError as exc:
        raise MCPAuthTokenVerificationException(
            MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
            cause=exc,
        ) from exc
    except ValueError as exc:
        raise MCPAuthTokenVerificationException(
            MCPAuthTokenVerificationExceptionCode.TOKEN_VERIFICATION_FAILED,
            cause=exc,
        ) from exc

    # Access tokens omit ``type``; refresh/reset carry ``type``.
    if payload.get("type") is not None:
        raise MCPAuthTokenVerificationException(
            MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
            cause=ValueError("typed tokens are not accepted as access tokens"),
        )

    user_id = payload.get("user_id")
    if user_id is None:
        try:
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MCPAuthTokenVerificationException(
                MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
                cause=exc,
            ) from exc

    subject = str(user_id)
    scopes = map_scopes_for_user(subject)
    issuer = auth_issuer_url()
    return AuthInfo(
        token=token,
        issuer=issuer,
        client_id=subject,
        subject=subject,
        scopes=scopes,
        audience=mcp_resource_url(),
        claims={
            "user_id": user_id,
            "sub": payload.get("sub"),
            "scopes": scopes,
        },
    )


def make_verify_fn() -> Callable[[str], AuthInfo]:
    return verify_brasaland_access_token
