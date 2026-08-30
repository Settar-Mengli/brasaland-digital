"""Renewable authentication for MCP-to-service HTTP requests."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

AUTH_ISSUER_ENV = "AUTH_ISSUER_URL"
SERVICE_CLIENT_ID_ENV = "MCP_SERVICE_CLIENT_ID"
SERVICE_CLIENT_SECRET_ENV = "MCP_SERVICE_CLIENT_SECRET"
TOKEN_ENDPOINT_PATH = "/auth/service-token"
TOKEN_RENEWAL_WINDOW_SECONDS = 30.0
TOKEN_RENEWAL_FRACTION = 0.1
TOKEN_REQUEST_TIMEOUT_SECONDS = 5.0

# Known limitation: downstream services see this fixed MCP service identity,
# not the human caller, so authorized reads can span the caller's locations.


class ServiceTokenError(RuntimeError):
    """Raised when the MCP service identity cannot obtain a valid access token."""


@dataclass(frozen=True)
class _ServiceCredentials:
    auth_origin: str
    client_id: str
    client_secret: str


@dataclass(frozen=True)
class _CachedServiceToken:
    access_token: str
    renew_at: float
    credentials: _ServiceCredentials


_cache_lock = threading.Lock()
_cached_token: _CachedServiceToken | None = None


def _monotonic() -> float:
    return time.monotonic()


def _service_credentials() -> _ServiceCredentials:
    client_id = os.environ.get(SERVICE_CLIENT_ID_ENV, "").strip()
    client_secret = os.environ.get(SERVICE_CLIENT_SECRET_ENV, "").strip()
    missing = [
        name
        for name, value in (
            (SERVICE_CLIENT_ID_ENV, client_id),
            (SERVICE_CLIENT_SECRET_ENV, client_secret),
        )
        if not value
    ]
    if missing:
        raise ServiceTokenError(
            f"{', '.join(missing)} required for downstream API calls"
        )

    auth_origin = os.environ.get(
        AUTH_ISSUER_ENV, "http://localhost:8002"
    ).rstrip("/")
    return _ServiceCredentials(
        auth_origin=auth_origin,
        client_id=client_id,
        client_secret=client_secret,
    )


def _acquire_service_token(
    credentials: _ServiceCredentials,
) -> _CachedServiceToken:
    with httpx.Client(timeout=TOKEN_REQUEST_TIMEOUT_SECONDS) as client:
        response = client.post(
            f"{credentials.auth_origin}{TOKEN_ENDPOINT_PATH}",
            auth=(credentials.client_id, credentials.client_secret),
        )

    if response.status_code != 200:
        raise ServiceTokenError(
            "service-token acquisition failed "
            f"with HTTP {response.status_code}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise ServiceTokenError(
            "service-token acquisition returned invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise ServiceTokenError(
            "service-token acquisition returned an invalid response"
        )

    access_token = payload.get("access_token")
    token_type = payload.get("token_type")
    expires_in = payload.get("expires_in")
    if (
        not isinstance(access_token, str)
        or not access_token
        or not isinstance(token_type, str)
        or token_type.lower() != "bearer"
        or not isinstance(expires_in, int)
        or isinstance(expires_in, bool)
        or expires_in <= 0
    ):
        raise ServiceTokenError(
            "service-token acquisition returned an invalid response"
        )

    now = _monotonic()
    renewal_lead = min(
        TOKEN_RENEWAL_WINDOW_SECONDS,
        expires_in * TOKEN_RENEWAL_FRACTION,
    )
    return _CachedServiceToken(
        access_token=access_token,
        renew_at=now + expires_in - renewal_lead,
        credentials=credentials,
    )


def service_access_token() -> str:
    """Return a cached service access token, renewing shortly before expiry."""
    credentials = _service_credentials()
    with _cache_lock:
        cached = _cached_token
        if (
            cached is not None
            and cached.credentials == credentials
            and _monotonic() < cached.renew_at
        ):
            return cached.access_token

        acquired = _acquire_service_token(credentials)
        _set_cached_token(acquired)
        return acquired.access_token


def _set_cached_token(token: _CachedServiceToken | None) -> None:
    global _cached_token
    _cached_token = token


def clear_service_token_cache() -> None:
    """Discard the cached token so the next request acquires a fresh one."""
    with _cache_lock:
        _set_cached_token(None)


def _invalidate_if_current(access_token: str) -> None:
    with _cache_lock:
        if (
            _cached_token is not None
            and _cached_token.access_token == access_token
        ):
            _set_cached_token(None)


def _send_authenticated_request(
    method: str,
    url: str,
    *,
    access_token: str,
    timeout: float,
    params: dict[str, Any] | None,
    json_body: Any | None,
) -> httpx.Response:
    request_kwargs: dict[str, Any] = {
        "headers": {"Authorization": f"Bearer {access_token}"},
    }
    if params is not None:
        request_kwargs["params"] = params
    if json_body is not None:
        request_kwargs["json"] = json_body

    with httpx.Client(timeout=timeout) as client:
        return client.request(method, url, **request_kwargs)


def request_with_service_token(
    method: str,
    url: str,
    *,
    timeout: float,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
) -> httpx.Response:
    """Send a downstream request and retry once with a fresh token on 401."""
    access_token = service_access_token()
    response = _send_authenticated_request(
        method,
        url,
        access_token=access_token,
        timeout=timeout,
        params=params,
        json_body=json_body,
    )
    if response.status_code != 401:
        return response

    _invalidate_if_current(access_token)
    replacement_token = service_access_token()
    return _send_authenticated_request(
        method,
        url,
        access_token=replacement_token,
        timeout=timeout,
        params=params,
        json_body=json_body,
    )
