"""Trusted-proxy rate-limit key resolution."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from brasaland_proxy_trust.rate_limit_key import (
    clear_trusted_proxy_cache,
    rate_limit_client_key,
)


@pytest.fixture(autouse=True)
def _reset_trust_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    clear_trusted_proxy_cache()


def _request(
    *,
    peer_host: str = "127.0.0.1",
    headers: dict[str, str] | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in (headers or {}).items()
        ],
        "client": (peer_host, 12345),
    }
    return Request(scope)


def test_spoofed_x_forwarded_for_ignored_when_peer_untrusted() -> None:
    request = _request(headers={"X-Forwarded-For": "203.0.113.1"})
    assert rate_limit_client_key(request) == "127.0.0.1"


def test_forwarded_for_used_when_peer_trusted_by_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_IPS", "127.0.0.1")
    clear_trusted_proxy_cache()
    request = _request(headers={"X-Forwarded-For": "203.0.113.1"})
    assert rate_limit_client_key(request) == "203.0.113.1"


def test_forwarded_for_used_when_peer_trusted_by_cidr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "127.0.0.0/8")
    clear_trusted_proxy_cache()
    request = _request(headers={"X-Forwarded-For": "198.51.100.44"})
    assert rate_limit_client_key(request) == "198.51.100.44"


def test_missing_forwarded_for_falls_back_to_peer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_IPS", "127.0.0.1")
    clear_trusted_proxy_cache()
    request = _request()
    assert rate_limit_client_key(request) == "127.0.0.1"


def test_leftmost_forwarded_for_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_IPS", "127.0.0.1")
    clear_trusted_proxy_cache()
    request = _request(
        headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.2"},
    )
    assert rate_limit_client_key(request) == "203.0.113.1"
