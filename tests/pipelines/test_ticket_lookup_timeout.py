"""Timeout bounds for agent→MCP ticket lookup."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipelines.tools import ticket_lookup as ticket_lookup_module
from pipelines.tools.ticket_lookup import lookup_ticket


@pytest.fixture(autouse=True)
def fast_mcp_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ticket_lookup_module, "MCP_AGENT_TIMEOUT_SECONDS", 0.01)


def test_mcp_get_tools_timeout_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8016/mcp")

    class FakeClient:
        async def get_tools(self) -> list[Any]:
            await asyncio.sleep(999)

    with patch(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        return_value=FakeClient(),
    ):
        result = lookup_ticket(
            {"ticket_ref": 42},
            access_token="test-token",
        )

    assert result["ok"] is False
    assert result["incidents"] == []
    assert result["matched_by"] is None
    assert result["error"] is not None
    assert "timed out" in result["error"].lower()


def test_mcp_ainvoke_timeout_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8016/mcp")

    async def hang(*_args: Any, **_kwargs: Any) -> None:
        await asyncio.sleep(999)

    hanging_tool = MagicMock()
    hanging_tool.name = ticket_lookup_module.MCP_TOOL_NAME
    hanging_tool.ainvoke = AsyncMock(side_effect=hang)

    class FakeClient:
        async def get_tools(self) -> list[Any]:
            return [hanging_tool]

    with patch(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        return_value=FakeClient(),
    ):
        result = lookup_ticket(
            {"ticket_ref": 42},
            access_token="test-token",
        )

    assert result["ok"] is False
    assert result["incidents"] == []
    assert result["matched_by"] is None
    assert result["error"] is not None
    assert "timed out" in result["error"].lower()
