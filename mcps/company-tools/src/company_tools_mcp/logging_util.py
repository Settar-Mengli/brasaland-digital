"""Tool invocation logging — never logs Bearer tokens or JWTs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("company_tools_mcp.invocation")

_SECRET_KEYS = frozenset(
    {
        "access_token",
        "token",
        "authorization",
        "bearer",
        "jwt",
        "password",
    }
)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if key.lower() in _SECRET_KEYS else _scrub(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str) and len(value) > 40 and value.count(".") == 2:
        # Heuristic JWT shape — never log raw tokens that slip into result strings.
        return "[REDACTED_POSSIBLE_JWT]"
    return value


def log_invocation(
    *,
    tool: str,
    client_user_id: str | None,
    result: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Log which tool ran, which client, and the outcome code/result."""
    payload = {
        "tool": tool,
        "client_user_id": client_user_id,
        "result": result,
    }
    if detail:
        payload["detail"] = _scrub(detail)
    logger.info("mcp_tool_invocation %s", payload)
