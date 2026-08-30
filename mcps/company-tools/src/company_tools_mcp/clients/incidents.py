"""HTTP client for services/incident-manager."""

from __future__ import annotations

import os
from typing import Any

from company_tools_mcp.clients.auth import request_with_service_token

TIMEOUT_S = 5.0


def incidents_origin() -> str:
    raw = os.environ.get("INCIDENTS_API_ORIGIN", "http://localhost:8011")
    return raw.rstrip("/")


def get_incident_by_id(incident_id: int) -> tuple[int, Any]:
    response = request_with_service_token(
        "GET",
        f"{incidents_origin()}/api/incidents/{incident_id}",
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None


def list_incidents(**filters: str) -> tuple[int, Any]:
    params = {key: value for key, value in filters.items() if value}
    response = request_with_service_token(
        "GET",
        f"{incidents_origin()}/api/incidents",
        params=params or None,
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None


def create_incident(body: dict[str, Any]) -> tuple[int, Any]:
    response = request_with_service_token(
        "POST",
        f"{incidents_origin()}/api/incidents",
        json_body=body,
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None


def patch_incident_status(incident_id: int, status: str) -> tuple[int, Any]:
    response = request_with_service_token(
        "PATCH",
        f"{incidents_origin()}/api/incidents/{incident_id}/status",
        json_body={"status": status},
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None
