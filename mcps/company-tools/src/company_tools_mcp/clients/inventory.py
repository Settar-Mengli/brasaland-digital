"""HTTP client for services/inventory — GET only; writes are rejected in tools."""

from __future__ import annotations

import os
from typing import Any

import httpx

from company_tools_mcp.clients.auth import service_auth_headers

TIMEOUT_S = 5.0


def inventory_origin() -> str:
    raw = os.environ.get("INVENTORY_API_ORIGIN", "http://localhost:8012")
    return raw.rstrip("/")


def list_products(location_id: int) -> tuple[int, Any]:
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.get(
            f"{inventory_origin()}/inventory/products",
            params={"location_id": location_id},
        )
        return response.status_code, response.json() if response.content else None


def get_product(ingredient_id: int, location_id: int) -> tuple[int, Any]:
    with httpx.Client(timeout=TIMEOUT_S, headers=service_auth_headers()) as client:
        response = client.get(
            f"{inventory_origin()}/inventory/products/{ingredient_id}",
            params={"location_id": location_id},
        )
        return response.status_code, response.json() if response.content else None
