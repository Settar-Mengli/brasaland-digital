"""Ticket lookup tool — live HTTP calls to incident-manager only.

Resolves a ticket ref that may be a numeric API ``id`` or an alphanumeric
``source_incident_id``. Numeric refs try GET /api/incidents/{id} first, then
match source_incident_id on the list. Non-numeric refs skip by-id (avoids 422)
and match source_incident_id only. Never fabricates status.
"""

from __future__ import annotations

import os
from typing import Any, Literal, TypedDict

import httpx

TICKET_LOOKUP_TIMEOUT_S = 5.0
INCIDENTS_ORIGIN_ENV = "INCIDENTS_API_ORIGIN"


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


def _origin() -> str | None:
    raw = os.environ.get(INCIDENTS_ORIGIN_ENV)
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


def lookup_ticket(inp: TicketLookupInput) -> TicketLookupResult:
    """Call the real incident-manager API. Never invents rows."""
    origin = _origin()
    if origin is None:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"{INCIDENTS_ORIGIN_ENV} is not set",
        )

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

    try:
        with httpx.Client(timeout=TICKET_LOOKUP_TIMEOUT_S) as client:
            if ticket_ref is not None:
                return _resolve_ref(client, origin, ticket_ref)
            return _list_filtered(client, origin, filters)
    except httpx.TimeoutException:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="incident-manager request timed out",
        )
    except httpx.RequestError as exc:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"incident-manager unreachable: {exc}",
        )


def _is_numeric_ref(ticket_ref: int | str) -> bool:
    if isinstance(ticket_ref, int):
        return True
    return str(ticket_ref).isdigit()


def _match_source_incident_id(
    client: httpx.Client, origin: str, needle: str
) -> TicketLookupResult:
    listed = client.get(f"{origin}/api/incidents")
    if listed.status_code != 200:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"incident-manager list HTTP {listed.status_code}",
        )
    rows = listed.json()
    if not isinstance(rows, list):
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="unexpected incident list payload",
        )
    matches = [
        _record_from_payload(row)
        for row in rows
        if isinstance(row, dict) and str(row.get("source_incident_id")) == needle
    ]
    if not matches:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="ticket not found",
        )
    return TicketLookupResult(
        ok=True,
        incidents=matches,
        matched_by="source_incident_id",
        error=None,
    )


def _resolve_ref(
    client: httpx.Client, origin: str, ticket_ref: int | str
) -> TicketLookupResult:
    # Non-numeric refs are source_incident_id values — skip by-id (avoids 422).
    if not _is_numeric_ref(ticket_ref):
        return _match_source_incident_id(client, origin, str(ticket_ref))

    by_id = client.get(f"{origin}/api/incidents/{ticket_ref}")
    if by_id.status_code == 200:
        payload = by_id.json()
        if not isinstance(payload, dict):
            return TicketLookupResult(
                ok=False,
                incidents=[],
                matched_by=None,
                error="unexpected incident payload",
            )
        return TicketLookupResult(
            ok=True,
            incidents=[_record_from_payload(payload)],
            matched_by="id",
            error=None,
        )
    if by_id.status_code != 404:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"incident-manager HTTP {by_id.status_code}",
        )

    return _match_source_incident_id(client, origin, str(ticket_ref))


def _list_filtered(
    client: httpx.Client, origin: str, filters: dict[str, Any]
) -> TicketLookupResult:
    response = client.get(f"{origin}/api/incidents", params=filters)
    if response.status_code != 200:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error=f"incident-manager HTTP {response.status_code}",
        )
    rows = response.json()
    if not isinstance(rows, list):
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="unexpected incident list payload",
        )
    incidents = [
        _record_from_payload(row) for row in rows if isinstance(row, dict)
    ]
    if not incidents:
        return TicketLookupResult(
            ok=False,
            incidents=[],
            matched_by=None,
            error="ticket not found",
        )
    return TicketLookupResult(
        ok=True,
        incidents=incidents,
        matched_by="filter",
        error=None,
    )
