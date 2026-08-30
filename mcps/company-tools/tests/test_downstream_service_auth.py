"""Renewable MCP service-identity tests for downstream HTTP clients."""

from __future__ import annotations

import base64
from collections.abc import Callable, Iterator

import httpx
import pytest
from company_tools_mcp.clients import auth as service_auth
from company_tools_mcp.clients import incidents, inventory


def _client_factory(
    real_client: type[httpx.Client],
    handler: Callable[[httpx.Request], httpx.Response],
) -> Callable[..., httpx.Client]:
    def factory(**kwargs: object) -> httpx.Client:
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    return factory


def _install_transport(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    real_client = httpx.Client
    monkeypatch.setattr(
        service_auth.httpx,
        "Client",
        _client_factory(real_client, handler),
    )


@pytest.fixture(autouse=True)
def _clear_token_cache() -> Iterator[None]:
    service_auth.clear_service_token_cache()
    yield
    service_auth.clear_service_token_cache()


@pytest.fixture
def service_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ISSUER_URL", "http://auth.test")
    monkeypatch.setenv("MCP_SERVICE_CLIENT_ID", "company-tools")
    monkeypatch.setenv("MCP_SERVICE_CLIENT_SECRET", "test-client-secret")


def test_all_downstream_requests_acquire_once_and_send_cached_bearer(
    monkeypatch: pytest.MonkeyPatch,
    service_credentials: None,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/auth/service-token":
            expected_basic = base64.b64encode(
                b"company-tools:test-client-secret"
            ).decode("ascii")
            assert request.method == "POST"
            assert request.headers["Authorization"] == f"Basic {expected_basic}"
            assert request.content == b""
            return httpx.Response(
                200,
                json={
                    "access_token": "service-access-1",
                    "token_type": "bearer",
                    "expires_in": 1800,
                },
            )
        if request.url.path.endswith("/api/incidents"):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={})

    _install_transport(monkeypatch, handler)

    incidents.get_incident_by_id(1)
    incidents.list_incidents(status="open")
    incidents.create_incident({"title": "test"})
    incidents.patch_incident_status(1, "in_progress")
    inventory.list_products(1)
    inventory.get_product(1, 1)

    token_requests = [
        request
        for request in requests
        if request.url.path == "/auth/service-token"
    ]
    downstream_requests = [
        request
        for request in requests
        if request.url.path != "/auth/service-token"
    ]
    assert len(token_requests) == 1
    assert len(downstream_requests) == 6
    assert {request.method for request in downstream_requests} == {
        "GET",
        "POST",
        "PATCH",
    }
    assert all(
        request.headers.get("Authorization")
        == "Bearer service-access-1"
        for request in downstream_requests
    )


def test_cached_token_renews_before_expiry(
    monkeypatch: pytest.MonkeyPatch,
    service_credentials: None,
) -> None:
    now = [1000.0]
    acquired = 0
    monkeypatch.setattr(service_auth, "_monotonic", lambda: now[0])

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal acquired
        assert request.url.path == "/auth/service-token"
        acquired += 1
        return httpx.Response(
            200,
            json={
                "access_token": f"service-access-{acquired}",
                "token_type": "bearer",
                "expires_in": 100,
            },
        )

    _install_transport(monkeypatch, handler)

    assert service_auth.service_access_token() == "service-access-1"
    now[0] = 1089.0
    assert service_auth.service_access_token() == "service-access-1"
    now[0] = 1090.0
    assert service_auth.service_access_token() == "service-access-2"
    assert acquired == 2


def test_downstream_401_reacquires_and_retries_once(
    monkeypatch: pytest.MonkeyPatch,
    service_credentials: None,
) -> None:
    acquired = 0
    downstream_bearers: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal acquired
        if request.url.path == "/auth/service-token":
            acquired += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"service-access-{acquired}",
                    "token_type": "bearer",
                    "expires_in": 1800,
                },
            )

        downstream_bearers.append(request.headers["Authorization"])
        if len(downstream_bearers) == 1:
            return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(200, json={"id": 1, "status": "open"})

    _install_transport(monkeypatch, handler)

    status_code, payload = incidents.get_incident_by_id(1)

    assert status_code == 200
    assert payload == {"id": 1, "status": "open"}
    assert acquired == 2
    assert downstream_bearers == [
        "Bearer service-access-1",
        "Bearer service-access-2",
    ]


def test_downstream_401_is_not_retried_more_than_once(
    monkeypatch: pytest.MonkeyPatch,
    service_credentials: None,
) -> None:
    acquired = 0
    downstream_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal acquired, downstream_calls
        if request.url.path == "/auth/service-token":
            acquired += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"service-access-{acquired}",
                    "token_type": "bearer",
                    "expires_in": 1800,
                },
            )

        downstream_calls += 1
        return httpx.Response(401, json={"detail": "unauthorized"})

    _install_transport(monkeypatch, handler)

    status_code, payload = inventory.get_product(1, 1)

    assert status_code == 401
    assert payload == {"detail": "unauthorized"}
    assert acquired == 2
    assert downstream_calls == 2


def test_downstream_requests_fail_closed_without_client_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MCP_SERVICE_CLIENT_ID", raising=False)
    monkeypatch.delenv("MCP_SERVICE_CLIENT_SECRET", raising=False)

    with pytest.raises(
        service_auth.ServiceTokenError,
        match="MCP_SERVICE_CLIENT_ID, MCP_SERVICE_CLIENT_SECRET required",
    ):
        incidents.get_incident_by_id(1)


def test_bad_client_credentials_fail_before_downstream_request(
    monkeypatch: pytest.MonkeyPatch,
    service_credentials: None,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/auth/service-token"
        return httpx.Response(401, json={"detail": "invalid service credentials"})

    _install_transport(monkeypatch, handler)

    with pytest.raises(
        service_auth.ServiceTokenError,
        match="service-token acquisition failed with HTTP 401",
    ):
        inventory.list_products(1)

    assert len(requests) == 1
