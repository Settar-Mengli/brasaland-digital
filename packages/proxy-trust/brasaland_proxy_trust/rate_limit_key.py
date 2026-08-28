"""Resolve the client IP for SlowAPI when requests pass through trusted proxies."""

from __future__ import annotations

import ipaddress
import os
from functools import lru_cache

from starlette.requests import Request


def _peer_host(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


@lru_cache(maxsize=1)
def _trusted_proxy_ips() -> frozenset[str]:
    raw = os.environ.get("TRUSTED_PROXY_IPS", "")
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


@lru_cache(maxsize=1)
def _trusted_proxy_networks() -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    raw = os.environ.get("TRUSTED_PROXY_CIDRS", "")
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for part in raw.split(","):
        candidate = part.strip()
        if not candidate:
            continue
        networks.append(ipaddress.ip_network(candidate, strict=False))
    return tuple(networks)


def _is_trusted_peer(host: str) -> bool:
    if host in _trusted_proxy_ips():
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(address in network for network in _trusted_proxy_networks())


def _client_ip_from_forwarded(header_value: str) -> str | None:
    for part in header_value.split(","):
        candidate = part.strip()
        if candidate:
            return candidate
    return None


def rate_limit_client_key(request: Request) -> str:
    """Return the rate-limit bucket key for ``request``.

    When the immediate peer is a configured trusted proxy, use the leftmost
    ``X-Forwarded-For`` value. Otherwise ignore forwarded headers and use the
    peer address (fail closed to per-connection identity, not an open bucket).
    """
    peer = _peer_host(request)
    if _is_trusted_peer(peer):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = _client_ip_from_forwarded(forwarded)
            if client_ip:
                return client_ip
    return peer


def clear_trusted_proxy_cache() -> None:
    """Clear cached trust config (tests only)."""
    _trusted_proxy_ips.cache_clear()
    _trusted_proxy_networks.cache_clear()
