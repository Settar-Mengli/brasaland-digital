from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Query, status

from cache import (
    DEFAULT_CACHE_KEY,
    TTL_SECONDS,
    explicit_cache_key,
    get_cached,
    set_cached,
)
from report_pipeline import run_report_pipeline

DEFAULT_PERIOD = timedelta(days=7)


def _format_period_iso(value: datetime) -> str:
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_query_datetime(value: str, param_name: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {param_name}: {value}",
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def resolve_report_period(
    start_date: str | None,
    end_date: str | None,
    now: datetime,
) -> tuple[datetime, datetime, tuple[str, ...], bool]:
    if start_date is None and end_date is None:
        end = now.astimezone(UTC)
        start = end - DEFAULT_PERIOD
        return start, end, DEFAULT_CACHE_KEY, True

    if start_date is None or end_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date and end_date must both be provided or both omitted",
        )

    start = _parse_query_datetime(start_date, "start_date")
    end = _parse_query_datetime(end_date, "end_date")
    return start, end, explicit_cache_key(start, end), False


def build_report_response(
    start_date: datetime,
    end_date: datetime,
    metrics: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "period": {
            "from": _format_period_iso(start_date),
            "to": _format_period_iso(end_date),
        },
        "metrics": metrics,
    }


def get_report_payload(
    start_date: str | None,
    end_date: str | None,
    now_fn: Callable[[], datetime],
    monotonic_fn: Callable[[], float],
) -> dict[str, Any]:
    now = now_fn().astimezone(UTC)
    period_start, period_end, cache_key, _uses_default = resolve_report_period(
        start_date,
        end_date,
        now,
    )

    cached = get_cached(cache_key, monotonic_fn)
    if cached is not None:
        return cached

    metrics = run_report_pipeline(period_start, period_end)
    payload = build_report_response(period_start, period_end, metrics)
    set_cached(cache_key, payload, monotonic_fn, ttl_seconds=TTL_SECONDS)
    return payload
