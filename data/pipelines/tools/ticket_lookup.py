"""Ticket lookup via company-tools MCP (check_ticket_status).

Replaces the former direct httpx path to incident-manager. The agent must
present a Bearer access token (forwarded from POST /agent/query). Dual id /
source_incident_id resolution lives on the MCP server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Literal, TypedDict

logger = logging.getLogger("pipelines.tools.ticket_lookup")

MCP_SERVER_URL_ENV = "MCP_SERVER_URL"
MCP_TOOL_NAME = "check_ticket_status"


class TicketLookupInput(TypedDict, total=False):
    ticket_ref: int | str | None
    status: str | None
    origin: str | None
    branch: str | None
    category: str | None


class TicketRecord(TypedDict):
    id: int
    source_incident_id: str
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class TicketLookupResult(TypedDict):
    ok: bool
    incidents: list[TicketRecord]
    matched_by: Literal["id", "source_incident_id", "filter"] | None
    error: str | None


def _mcp_url() -> str | None:
    raw = os.environ.get(MCP_SERVER_URL_ENV)
    if raw is None or not raw.strip():
        return None
    return raw.rstrip("/")


def _record_from_payload(payload: dict[str, Any]) -> TicketRecord:
    return TicketRecord(
        id=int(payload["id"]),
        source_incident_id=str(payload["source_incident_id"]),
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
        category=str(payload.get("category") or ""),
        status=str(payload.get("status") or ""),
        origin=str(payload.get("origin") or ""),
        branch=str(payload.get("branch") or ""),
        created_at=str(payload.get("created_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


def format_ticket_answer(incidents: list[TicketRecord]) -> str:
    """Deterministic formatter — status/category/dates never pass through an LLM."""
    if not incidents:
        return ""
    parts: list[str] = []
    for row in incidents:
        parts.append(
            "Ticket "
            f"{row['source_incident_id']} (id {row['id']}): "
            f"status={row['status']}, category={row['category']}, "
            f"origin={row['origin']}, branch={row['branch']}, "
            f"created_at={row['created_at']}, updated_at={row['updated_at']}."
        )
    return " ".join(parts)


def _parse_tool_content(raw: Any) -> dict[str, Any]:
    """Unwrap langchain-mcp-adapters content blocks to the tool JSON dict.

    FastMCP dict returns arrive as
    ``[{"type": "text", "text": "<json>", "id": "..."}]`` — not a bare dict.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        text = None
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                candidate = block.get("text")
                if isinstance(candidate, str) and candidate.strip():
                    text = candidate
                    break
        if text is None:
            return {"ok": False, "message": "MCP tool returned no text content"}
        raw = text
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": False, "message": raw}
        if isinstance(parsed, dict):
            return parsed
        return {"ok": False, "message": "MCP tool text was not a JSON object"}
    return {
        "ok": False,
        "message": f"unexpected MCP tool result type: {type(raw).__name__}",
    }


async def _ainvoke_check_ticket(
    *, access_token: str, ticket_ref: str
) -> TicketLookupResult:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    url = _mcp_url()
    if url is None:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"{MCP_SERVER_URL_ENV} is not set",
        )

    client = MultiServerMCPClient(
        {
            "company_tools": {
                "transport": "streamable_http",
                "url": url,
                "headers": {"Authorization": f"Bearer {access_token}"},
            }
        }
    )
    tools = await client.get_tools()
    tool = next((item for item in tools if item.name == MCP_TOOL_NAME), None)
    if tool is None:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"MCP tool {MCP_TOOL_NAME} not found",
        )

    raw = await tool.ainvoke({"ticket_ref": ticket_ref})
    payload = _parse_tool_content(raw)
    if not payload.get("ok"):
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=str(
                payload.get("code")
                or payload.get("message")
                or "MCP ticket lookup failed"
            ),
        )
    incident = payload.get("incident")
    if not isinstance(incident, dict):
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="unexpected MCP ticket payload",
        )
    matched = payload.get("matched_by")
    matched_by: Literal["id", "source_incident_id", "filter"] | None
    if matched in ("id", "source_incident_id", "filter"):
        matched_by = matched  # type: ignore[assignment]
    else:
        matched_by = "id"
    return TicketLookupResult(
        ok=True,
        incidents=[_record_from_payload(incident)],
        matched_by=matched_by,
        error=None,
    )


def lookup_ticket(
    inp: TicketLookupInput,
    *,
    access_token: str | None = None,
) -> TicketLookupResult:
    """Call company-tools MCP check_ticket_status. Never invents rows."""
    ticket_ref = inp.get("ticket_ref")
    filters = {
        key: inp.get(key)
        for key in ("status", "origin", "branch", "category")
        if inp.get(key)
    }
    if ticket_ref is None and not filters:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="ticket_ref or at least one filter is required",
        )
    if access_token is None or not str(access_token).strip():
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="access_token is required for MCP ticket lookup",
        )
    if ticket_ref is None:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="filter-only ticket lookup is not exposed via MCP in this release",
        )

    ref = str(ticket_ref)
    # Never log the Bearer token.
    logger.info(
        "mcp_ticket_lookup client_call tool=%s ticket_ref=%s",
        MCP_TOOL_NAME,
        ref,
    )
    try:
        return asyncio.run(
            _ainvoke_check_ticket(access_token=access_token, ticket_ref=ref)
        )
    except RuntimeError:
        # Already inside a running loop (e.g. some test runners).
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                _ainvoke_check_ticket(access_token=access_token, ticket_ref=ref)
            )
        finally:
            loop.close()
    except Exception as exc:  # noqa: BLE001
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"MCP ticket lookup failed: {exc}",
        )
