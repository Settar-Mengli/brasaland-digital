"""HTTP client for services/incident-manager."""

from __future__ import annotations

import os
from typing import Any

import httpx

from company_tools_mcp.clients.auth import service_auth_headers

TIMEOUT_S = 5.0


def incidents_origin() -> str:
    raw = os.environ.get("INCIDENTS_API_ORIGIN", "http://localhost:8011")
    return raw.rstrip("/")


def get_incident_by_id(incident_id: int) -> tuple[int, Any]:
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.get(f"{incidents_origin()}/api/incidents/{incident_id}")
        return response.status_code, response.json() if response.content else None


def list_incidents(**filters: str) -> tuple[int, Any]:
    params = {key: value for key, value in filters.items() if value}
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.get(
            f"{incidents_origin()}/api/incidents",
            params=params or None,
        )
        return response.status_code, response.json() if response.content else None


def create_incident(body: dict[str, Any]) -> tuple[int, Any]:
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.post(f"{incidents_origin()}/api/incidents", json=body)
        return response.status_code, response.json() if response.content else None


def patch_incident_status(incident_id: int, status: str) -> tuple[int, Any]:
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.patch(
            f"{incidents_origin()}/api/incidents/{incident_id}/status",
            json={"status": status},
        )
        return response.status_code, response.json() if response.content else None
