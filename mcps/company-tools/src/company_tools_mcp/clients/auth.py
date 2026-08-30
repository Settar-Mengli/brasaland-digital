"""Authentication for MCP-to-service HTTP requests."""

from __future__ import annotations

import os

SERVICE_TOKEN_ENV = "MCP_SERVICE_TOKEN"


def service_auth_headers() -> dict[str, str]:
    """Return the dedicated downstream service-account Bearer header."""
    token = os.environ.get(SERVICE_TOKEN_ENV, "").strip()
    if not token:
        raise RuntimeError(f"{SERVICE_TOKEN_ENV} is required for downstream API calls")

    # Known limitation: this fixed MCP identity replaces the caller downstream,
    # so authorized inventory/incident reads can span locations regardless of caller.
    return {"Authorization": f"Bearer {token}"}
