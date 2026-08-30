"""HTTP client for services/inventory — GET only; writes are rejected in tools."""

from __future__ import annotations

import os
from typing import Any

from company_tools_mcp.clients.auth import request_with_service_token

TIMEOUT_S = 5.0


def inventory_origin() -> str:
    raw = os.environ.get("INVENTORY_API_ORIGIN", "http://localhost:8012")
    return raw.rstrip("/")


def list_products(location_id: int) -> tuple[int, Any]:
    response = request_with_service_token(
        "GET",
        f"{inventory_origin()}/inventory/products",
        params={"location_id": location_id},
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None


def get_product(ingredient_id: int, location_id: int) -> tuple[int, Any]:
    response = request_with_service_token(
        "GET",
        f"{inventory_origin()}/inventory/products/{ingredient_id}",
        params={"location_id": location_id},
        timeout=TIMEOUT_S,
    )
    return response.status_code, response.json() if response.content else None
