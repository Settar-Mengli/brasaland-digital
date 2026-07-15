"""Pure KPI transforms for the weekly location performance report.

No Prefect decorators and no database imports — Part 3 can unit-test these
functions in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from statistics import median
from typing import Any, Mapping, Sequence

from pipelines.locations import (
    LOCATION_DIMENSIONS,
    PRICE_ALERT_BASELINE_WEEKS,
    PRICE_ALERT_THRESHOLD_PCT,
)

EVENT_SUPPLY = "supply_order_created"
EVENT_CONSUMPTION = "consumption_order_created"
EVENT_STOCKOUT = "stock_threshold_triggered"


@dataclass(frozen=True)
class LocationWeekRow:
    """In-memory destination row for one (location_id, week_start)."""

    location_id: str
    country: str
    week_start: date
    total_purchase_cost: Decimal
    total_waste_cost: Decimal
    waste_ratio: Decimal
    stockout_events_count: int
    price_alert_events_count: int
    currency: str


@dataclass(frozen=True)
class TransformResult:
    """KPI rows plus data-quality counters for a single week."""

    rows: list[LocationWeekRow]
    missing_cost_events_count: int


def _as_dict(tags: Any) -> dict[str, Any]:
    if tags is None:
        return {}
    if isinstance(tags, Mapping):
        return dict(tags)
    return {}


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    return None


def _in_window(ts: datetime, week_start: date, week_end: date) -> bool:
    start = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    end = datetime(week_end.year, week_end.month, week_end.day, tzinfo=timezone.utc)
    return start <= ts < end


def compute_purchase_costs(
    records: Sequence[Mapping[str, Any]],
    week_start: date,
) -> tuple[dict[str, Decimal], int]:
    """Sum quantity * unit_cost for supply_order_created in the target week.

    Missing or non-numeric unit_cost contributes 0 to the sum and increments
    the missing-cost counter.
    """
    week_end = week_start + timedelta(days=7)
    totals: dict[str, Decimal] = {slug: Decimal("0") for slug in LOCATION_DIMENSIONS}
    missing = 0

    for record in records:
        if record.get("event_type") != EVENT_SUPPLY:
            continue
        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None or not _in_window(ts, week_start, week_end):
            continue
        tags = _as_dict(record.get("tags"))
        location_id = tags.get("location_id")
        if location_id not in LOCATION_DIMENSIONS:
            continue
        quantity = _as_number(tags.get("quantity"))
        unit_cost = _as_number(tags.get("unit_cost"))
        if quantity is None:
            continue
        if unit_cost is None:
            missing += 1
            continue
        totals[location_id] += Decimal(str(quantity)) * Decimal(str(unit_cost))

    return totals, missing


def compute_waste_costs(
    records: Sequence[Mapping[str, Any]],
    week_start: date,
) -> tuple[dict[str, Decimal], int]:
    """Value waste exits at the latest prior supply unit_cost for the pair.

    Waste = consumption_order_created with tags.reason == 'waste'. Valuation uses
    the most recent cost-bearing supply_order_created for (ingredient_id,
    location_id) at or before the waste timestamp. Missing cost → 0 and DQ bump.
    """
    week_end = week_start + timedelta(days=7)
    supplies: list[tuple[datetime, str, str, float]] = []
    for record in records:
        if record.get("event_type") != EVENT_SUPPLY:
            continue
        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None:
            continue
        tags = _as_dict(record.get("tags"))
        location_id = tags.get("location_id")
        ingredient_id = tags.get("ingredient_id")
        unit_cost = _as_number(tags.get("unit_cost"))
        if (
            location_id not in LOCATION_DIMENSIONS
            or ingredient_id is None
            or unit_cost is None
        ):
            continue
        supplies.append((ts, str(location_id), str(ingredient_id), unit_cost))
    supplies.sort(key=lambda item: item[0])

    totals: dict[str, Decimal] = {slug: Decimal("0") for slug in LOCATION_DIMENSIONS}
    missing = 0

    for record in records:
        if record.get("event_type") != EVENT_CONSUMPTION:
            continue
        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None or not _in_window(ts, week_start, week_end):
            continue
        tags = _as_dict(record.get("tags"))
        if tags.get("reason") != "waste":
            continue
        location_id = tags.get("location_id")
        ingredient_id = tags.get("ingredient_id")
        quantity = _as_number(tags.get("quantity"))
        if location_id not in LOCATION_DIMENSIONS or ingredient_id is None or quantity is None:
            continue

        latest_cost: float | None = None
        for supply_ts, supply_loc, supply_ing, supply_cost in supplies:
            if supply_ts > ts:
                break
            if supply_loc == location_id and supply_ing == str(ingredient_id):
                latest_cost = supply_cost
        if latest_cost is None:
            missing += 1
            continue
        totals[location_id] += Decimal(str(quantity)) * Decimal(str(latest_cost))

    return totals, missing


def compute_waste_ratio(purchase: Decimal, waste: Decimal) -> Decimal:
    """Return waste / purchase, or 0 when there were no purchases."""
    if purchase == 0:
        return Decimal("0")
    return waste / purchase


def compute_stockout_counts(
    records: Sequence[Mapping[str, Any]],
    week_start: date,
) -> dict[str, int]:
    """Count stock_threshold_triggered events per location in the target week."""
    week_end = week_start + timedelta(days=7)
    counts: dict[str, int] = {slug: 0 for slug in LOCATION_DIMENSIONS}
    for record in records:
        if record.get("event_type") != EVENT_STOCKOUT:
            continue
        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None or not _in_window(ts, week_start, week_end):
            continue
        tags = _as_dict(record.get("tags"))
        location_id = tags.get("location_id")
        if location_id in LOCATION_DIMENSIONS:
            counts[location_id] += 1
    return counts


def compute_price_alert_counts(
    records: Sequence[Mapping[str, Any]],
    week_start: date,
) -> dict[str, int]:
    """Count supply orders whose unit_cost exceeds the trailing median baseline.

    Baseline = median of cost-bearing supply_order_created for the same
    (ingredient_id, location_id) over the prior PRICE_ALERT_BASELINE_WEEKS
    exclusive of the target week. Alert when |cost - baseline| / baseline >
    PRICE_ALERT_THRESHOLD_PCT / 100. Fewer than 2 prior events → never alert.
    """
    week_end = week_start + timedelta(days=7)
    baseline_start = week_start - timedelta(weeks=PRICE_ALERT_BASELINE_WEEKS)
    threshold = PRICE_ALERT_THRESHOLD_PCT / 100.0

    history: dict[tuple[str, str], list[float]] = {}
    week_supplies: list[tuple[str, str, float]] = []

    for record in records:
        if record.get("event_type") != EVENT_SUPPLY:
            continue
        ts = _parse_timestamp(record.get("timestamp"))
        if ts is None:
            continue
        tags = _as_dict(record.get("tags"))
        location_id = tags.get("location_id")
        ingredient_id = tags.get("ingredient_id")
        unit_cost = _as_number(tags.get("unit_cost"))
        if (
            location_id not in LOCATION_DIMENSIONS
            or ingredient_id is None
            or unit_cost is None
        ):
            continue
        key = (str(location_id), str(ingredient_id))
        if _in_window(ts, baseline_start, week_start):
            history.setdefault(key, []).append(unit_cost)
        elif _in_window(ts, week_start, week_end):
            week_supplies.append((str(location_id), str(ingredient_id), unit_cost))

    counts: dict[str, int] = {slug: 0 for slug in LOCATION_DIMENSIONS}
    for location_id, ingredient_id, unit_cost in week_supplies:
        prior = history.get((location_id, ingredient_id), [])
        if len(prior) < 2:
            continue
        baseline = float(median(prior))
        if baseline == 0:
            continue
        if abs(unit_cost - baseline) / baseline > threshold:
            counts[location_id] += 1
    return counts


def transform_week(
    records: Sequence[Mapping[str, Any]],
    week_start: date,
) -> TransformResult:
    """Build all 14 location KPI rows and aggregate missing-cost counts for a week."""
    purchase, missing_purchase = compute_purchase_costs(records, week_start)
    waste, missing_waste = compute_waste_costs(records, week_start)
    stockouts = compute_stockout_counts(records, week_start)
    price_alerts = compute_price_alert_counts(records, week_start)

    rows: list[LocationWeekRow] = []
    for location_id, (country, currency) in LOCATION_DIMENSIONS.items():
        purchase_cost = purchase[location_id]
        waste_cost = waste[location_id]
        rows.append(
            LocationWeekRow(
                location_id=location_id,
                country=country,
                week_start=week_start,
                total_purchase_cost=purchase_cost,
                total_waste_cost=waste_cost,
                waste_ratio=compute_waste_ratio(purchase_cost, waste_cost),
                stockout_events_count=stockouts[location_id],
                price_alert_events_count=price_alerts[location_id],
                currency=currency,
            )
        )

    return TransformResult(
        rows=rows,
        missing_cost_events_count=missing_purchase + missing_waste,
    )
