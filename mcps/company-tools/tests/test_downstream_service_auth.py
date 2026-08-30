"""MCP downstream clients attach the dedicated service-account token."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from company_tools_mcp.clients import incidents, inventory


def _client_factory(
    real_client: type[httpx.Client],
    handler: Callable[[httpx.Request], httpx.Response],
) -> Callable[..., httpx.Client]:
    def factory(**kwargs: object) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    return factory


def test_all_downstream_requests_send_service_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_SERVICE_TOKEN", "dedicated-service-token")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/api/incidents"):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={})

    real_client = httpx.Client
    factory = _client_factory(real_client, handler)
    monkeypatch.setattr(incidents.httpx, "Client", factory)
    monkeypatch.setattr(inventory.httpx, "Client", factory)

    incidents.get_incident_by_id(1)
    incidents.list_incidents(status="open")
    incidents.create_incident({"title": "test"})
    incidents.patch_incident_status(1, "in_progress")
    inventory.list_products(1)
    inventory.get_product(1, 1)

    assert len(requests) == 6
    assert {request.method for request in requests} == {"GET", "POST", "PATCH"}
    assert all(
        request.headers.get("Authorization") == "Bearer dedicated-service-token"
        for request in requests
    )


def test_downstream_requests_fail_closed_without_service_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_SERVICE_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="MCP_SERVICE_TOKEN is required"):
        incidents.get_incident_by_id(1)
