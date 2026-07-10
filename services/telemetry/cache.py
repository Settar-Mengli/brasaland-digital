from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

DEFAULT_CACHE_KEY: tuple[str] = ("__default__",)
TTL_SECONDS = 60

_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}


def explicit_cache_key(start_date: datetime, end_date: datetime) -> tuple[str, str]:
    return (start_date.isoformat(), end_date.isoformat())


def get_cached(
    key: tuple[str, ...],
    now_fn: Callable[[], float],
) -> dict[str, Any] | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, payload = entry
    if now_fn() >= expires_at:
        _cache.pop(key, None)
        return None
    return payload


def set_cached(
    key: tuple[str, ...],
    payload: dict[str, Any],
    now_fn: Callable[[], float],
    ttl_seconds: float = TTL_SECONDS,
) -> None:
    _cache[key] = (now_fn() + ttl_seconds, payload)


def clear_cache() -> None:
    _cache.clear()
