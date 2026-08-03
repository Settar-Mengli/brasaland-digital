"""Ticket tool unit tests with mocked incident-manager HTTP."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from company_tools_mcp.errors import AUTHZ_SCOPE_DENIED, VALIDATION_ERROR
from company_tools_mcp.tools.tickets import (
    check_ticket_status_impl,
    create_ticket_impl,
    update_ticket_status_impl,
)
from tests.conftest import make_auth_info


def test_baseline_cannot_create_ticket(baseline_auth: MagicMock) -> None:
    result = create_ticket_impl(
        baseline_auth,
        title="t",
        description="d",
        category="EQUIPAMIENTO",
        status="open",
        origin="branch",
        branch="COL-01",
    )
    assert result["code"] == AUTHZ_SCOPE_DENIED


def test_create_requires_all_required_fields(writer_auth: MagicMock) -> None:
    result = create_ticket_impl(
        writer_auth,
        title="",
        description="d",
        category="EQUIPAMIENTO",
        status="open",
        origin="branch",
        branch="COL-01",
    )
    assert result["code"] == VALIDATION_ERROR
    assert "title" in result["fields"]


def test_create_ticket_proxies_post(writer_auth: MagicMock) -> None:
    incident = {
        "id": 1,
        "source_incident_id": "MANUAL-1",
        "title": "t",
        "description": "d",
        "category": "EQUIPAMIENTO",
        "status": "open",
        "origin": "branch",
        "branch": "COL-01",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    with patch(
        "company_tools_mcp.tools.tickets.incidents_client.create_incident",
        return_value=(201, incident),
    ) as mocked:
        result = create_ticket_impl(
            writer_auth,
            title="t",
            description="d",
            category="EQUIPAMIENTO",
            status="open",
            origin="branch",
            branch="COL-01",
        )
    assert result["ok"] is True
    mocked.assert_called_once()
    body = mocked.call_args.args[0]
    assert body["status"] == "open"
    assert set(body.keys()) >= {
        "title",
        "description",
        "category",
        "status",
        "origin",
        "branch",
    }


def test_update_uses_status_patch_only(writer_auth: MagicMock) -> None:
    with patch(
        "company_tools_mcp.tools.tickets.incidents_client.patch_incident_status",
        return_value=(200, {"id": 9, "status": "in_progress"}),
    ) as mocked:
        result = update_ticket_status_impl(
            writer_auth, incident_id=9, status="in_progress"
        )
    assert result["ok"] is True
    mocked.assert_called_once_with(9, "in_progress")


def test_check_ticket_by_id(baseline_auth: MagicMock) -> None:
    payload = {
        "id": 98,
        "source_incident_id": "MANUAL-98",
        "title": "x",
        "description": "y",
        "category": "PERSONAL",
        "status": "open",
        "origin": "branch",
        "branch": "FLA-01",
        "created_at": "a",
        "updated_at": "b",
    }
    with patch(
        "company_tools_mcp.tools.tickets.incidents_client.get_incident_by_id",
        return_value=(200, payload),
    ):
        result = check_ticket_status_impl(baseline_auth, "98")
    assert result["ok"] is True
    assert result["matched_by"] == "id"
