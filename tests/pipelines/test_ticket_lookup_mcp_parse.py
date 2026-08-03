"""Unit tests for MCP tool content-block unwrap → TicketLookupResult mapping."""

from __future__ import annotations

from pipelines.tools.ticket_lookup import (
    TicketLookupResult,
    _parse_tool_content,
    _record_from_payload,
)


def _result_from_payload(payload: dict) -> TicketLookupResult:
    """Mirror _ainvoke_check_ticket mapping after parse (no network)."""
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
    matched_by = matched if matched in ("id", "source_incident_id", "filter") else "id"
    return TicketLookupResult(
        ok=True,
        incidents=[_record_from_payload(incident)],
        matched_by=matched_by,  # type: ignore[arg-type]
        error=None,
    )


_SAMPLE_INCIDENT = {
    "id": 98,
    "source_incident_id": "MANUAL-98",
    "title": "Grill outage",
    "description": "Main grill down",
    "category": "EQUIPAMIENTO",
    "status": "in_progress",
    "origin": "branch",
    "branch": "COL-01",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def test_parse_success_content_block_list() -> None:
    text = (
        '{"ok":true,"incident":'
        + __import__("json").dumps(_SAMPLE_INCIDENT)
        + ',"matched_by":"id"}'
    )
    raw = [{"type": "text", "text": text, "id": "lc_1"}]
    payload = _parse_tool_content(raw)
    result = _result_from_payload(payload)
    assert result["ok"] is True
    assert result["error"] is None
    assert result["matched_by"] == "id"
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["id"] == 98
    assert result["incidents"][0]["source_incident_id"] == "MANUAL-98"


def test_parse_error_content_block_list_authz() -> None:
    text = (
        '{"ok":false,"code":"AUTHZ_SCOPE_DENIED",'
        '"message":"Missing required scopes: tickets:write"}'
    )
    raw = [{"type": "text", "text": text, "id": "lc_2"}]
    payload = _parse_tool_content(raw)
    result = _result_from_payload(payload)
    assert result["ok"] is False
    assert result["incidents"] == []
    assert "AUTHZ_SCOPE_DENIED" in (result["error"] or "")
    assert "[{'type'" not in (result["error"] or "")


def test_parse_empty_or_non_text_list() -> None:
    assert _parse_tool_content([])["message"] == "MCP tool returned no text content"
    assert (
        _parse_tool_content([{"type": "image", "base64": "x"}])["message"]
        == "MCP tool returned no text content"
    )
    assert (
        _parse_tool_content([{"type": "text", "text": "   "}])["message"]
        == "MCP tool returned no text content"
    )


def test_parse_dict_passthrough() -> None:
    raw = {
        "ok": True,
        "incident": _SAMPLE_INCIDENT,
        "matched_by": "source_incident_id",
    }
    payload = _parse_tool_content(raw)
    result = _result_from_payload(payload)
    assert result["ok"] is True
    assert result["matched_by"] == "source_incident_id"
    assert result["incidents"][0]["id"] == 98
