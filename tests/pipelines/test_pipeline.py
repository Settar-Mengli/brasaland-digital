"""Unit tests for weekly KPI transforms (no DB / no Prefect).

Run from the data env with a single-path target to avoid root ImportPathMismatch::

    uv run --directory data pytest ../tests/pipelines/test_pipeline.py
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from pipelines.transform import (
    compute_price_alert_counts,
    compute_purchase_costs,
    compute_waste_ratio,
    transform_week,
)

WEEK_START = date(2026, 7, 6)  # Monday
LOCATION = "medellin_centro"


def _ts(day_offset: int, hour: int = 12) -> datetime:
    return datetime(
        WEEK_START.year,
        WEEK_START.month,
        WEEK_START.day,
        hour,
        0,
        0,
        tzinfo=timezone.utc,
    ) + timedelta(days=day_offset)


def _ctx() -> dict[str, str]:
    return {
        "sessionId": "session-test",
        "userId": "42",
        "requestId": "req-test",
        "schemaVersion": "2.1.0",
    }


def _supply(
    event_id: str,
    ts: datetime,
    *,
    quantity: float,
    unit_cost: Any,
    ingredient_id: str = "ing-beef",
    location_id: str = LOCATION,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_type": "supply_order_created",
        "timestamp": ts,
        "tags": {
            "location_id": location_id,
            "ingredient_id": ingredient_id,
            "quantity": quantity,
            "unit_cost": unit_cost,
        },
        "context": _ctx(),
    }


def _waste(
    event_id: str,
    ts: datetime,
    *,
    quantity: float,
    ingredient_id: str = "ing-beef",
    location_id: str = LOCATION,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_type": "consumption_order_created",
        "timestamp": ts,
        "tags": {
            "location_id": location_id,
            "ingredient_id": ingredient_id,
            "quantity": quantity,
            "reason": "waste",
        },
        "context": _ctx(),
    }


def test_defensive_null_and_non_numeric_unit_cost() -> None:
    """Null / wrong-type unit_cost contributes 0 and bumps missing_cost; no throw."""
    records = [
        _supply("e-null", _ts(0), quantity=10, unit_cost=None),
        _supply("e-str", _ts(0, 13), quantity=5, unit_cost="not-a-number"),
        _supply("e-ok", _ts(0, 14), quantity=2, unit_cost=100.0),
    ]
    totals, missing = compute_purchase_costs(records, WEEK_START)
    assert missing == 2
    assert totals[LOCATION] == Decimal("200")
    result = transform_week(records, WEEK_START)
    assert result.missing_cost_events_count >= 2
    row = next(r for r in result.rows if r.location_id == LOCATION)
    assert row.total_purchase_cost == Decimal("200")


def test_hand_calculated_purchase_waste_and_ratio() -> None:
    """Known supply + waste events → exact purchase, waste, and waste_ratio."""
    # Purchase: 10 * 50 = 500
    # Waste: 2 * 50 (latest supply cost) = 100
    # Ratio: 100/500 = 0.2
    records = [
        _supply("s1", _ts(0), quantity=10, unit_cost=50.0),
        _waste("w1", _ts(1), quantity=2),
    ]
    result = transform_week(records, WEEK_START)
    row = next(r for r in result.rows if r.location_id == LOCATION)
    assert row.total_purchase_cost == Decimal("500")
    assert row.total_waste_cost == Decimal("100")
    assert row.waste_ratio == Decimal("0.2")


def test_price_alert_median_deviation_fires() -> None:
    """Unit cost > median baseline by more than ±25% with ≥2 prior events → alert."""
    prior_week_1 = WEEK_START - timedelta(weeks=2)
    prior_week_2 = WEEK_START - timedelta(weeks=3)
    # Prior costs: 100, 100 → median 100. Target week: 130 → +30% → alert.
    records = [
        _supply(
            "p1",
            datetime(
                prior_week_1.year,
                prior_week_1.month,
                prior_week_1.day,
                12,
                tzinfo=timezone.utc,
            ),
            quantity=1,
            unit_cost=100.0,
        ),
        _supply(
            "p2",
            datetime(
                prior_week_2.year,
                prior_week_2.month,
                prior_week_2.day,
                12,
                tzinfo=timezone.utc,
            ),
            quantity=1,
            unit_cost=100.0,
        ),
        _supply("t1", _ts(0), quantity=1, unit_cost=130.0),
    ]
    counts = compute_price_alert_counts(records, WEEK_START)
    assert counts[LOCATION] == 1


def test_price_alert_min_two_prior_events_never_alerts() -> None:
    """Fewer than 2 prior cost-bearing events → never alert."""
    prior = WEEK_START - timedelta(weeks=2)
    records = [
        _supply(
            "p-only-one",
            datetime(prior.year, prior.month, prior.day, 12, tzinfo=timezone.utc),
            quantity=1,
            unit_cost=100.0,
        ),
        _supply("t-spike", _ts(0), quantity=1, unit_cost=200.0),
    ]
    counts = compute_price_alert_counts(records, WEEK_START)
    assert counts[LOCATION] == 0


def test_zero_purchase_waste_ratio_is_zero() -> None:
    """When purchases are 0, waste_ratio is 0 (not division-by-zero)."""
    assert compute_waste_ratio(Decimal("0"), Decimal("100")) == Decimal("0")
    # Waste with no cost-bearing supply in window → waste cost 0, purchases 0.
    records = [_waste("w-only", _ts(0), quantity=5)]
    result = transform_week(records, WEEK_START)
    row = next(r for r in result.rows if r.location_id == LOCATION)
    assert row.total_purchase_cost == Decimal("0")
    assert row.waste_ratio == Decimal("0")
