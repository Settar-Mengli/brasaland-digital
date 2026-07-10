from __future__ import annotations

from datetime import UTC, datetime

from analysis import (
    auth_failure_rate_per_day,
    consumption_by_location_per_day,
    order_failure_rate_per_day,
)
from tests.conftest import seed_row


def test_consumption_groups_two_locations_two_days() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 3, tzinfo=UTC)
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 1, 10, tzinfo=UTC),
        {"location_id": "medellin_centro", "ingredient_id": 1, "quantity": 1, "reason": "consumption", "consumption_order_id": 1, "created_by": "1", "restricted_access": False},
    )
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 1, 11, tzinfo=UTC),
        {"location_id": "miami_brickell", "ingredient_id": 2, "quantity": 1, "reason": "consumption", "consumption_order_id": 2, "created_by": "1", "restricted_access": False},
    )
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 2, 10, tzinfo=UTC),
        {"location_id": "medellin_centro", "ingredient_id": 3, "quantity": 1, "reason": "consumption", "consumption_order_id": 3, "created_by": "1", "restricted_access": False},
    )
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 2, 11, tzinfo=UTC),
        {"location_id": "miami_brickell", "ingredient_id": 4, "quantity": 1, "reason": "consumption", "consumption_order_id": 4, "created_by": "1", "restricted_access": False},
    )

    result = consumption_by_location_per_day(start, end)
    assert sorted(result, key=lambda row: (row["date"], row["location_id"])) == [
        {"date": "2026-07-01", "location_id": "medellin_centro", "count": 1},
        {"date": "2026-07-01", "location_id": "miami_brickell", "count": 1},
        {"date": "2026-07-02", "location_id": "medellin_centro", "count": 1},
        {"date": "2026-07-02", "location_id": "miami_brickell", "count": 1},
    ]


def test_consumption_drops_null_location_id() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 2, tzinfo=UTC)
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 1, 10, tzinfo=UTC),
        {"ingredient_id": 1, "quantity": 1, "reason": "consumption", "consumption_order_id": 1, "created_by": "1", "restricted_access": False},
    )

    assert consumption_by_location_per_day(start, end) == []


def test_order_failure_rate_computes_ratio() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 2, tzinfo=UTC)
    day = datetime(2026, 7, 1, 12, tzinfo=UTC)
    seed_row("supply_order_created", day, {"supply_order_id": 1, "ingredient_id": 1, "quantity": 1, "supplier_id": 0, "location_id": "medellin_centro", "created_by": "1"})
    seed_row("consumption_order_created", day, {"consumption_order_id": 2, "ingredient_id": 2, "quantity": 1, "reason": "consumption", "location_id": "medellin_centro", "created_by": "1", "restricted_access": False})
    seed_row("supply_order_created", day, {"supply_order_id": 3, "ingredient_id": 3, "quantity": 1, "supplier_id": 0, "location_id": "medellin_centro", "created_by": "1"})
    seed_row("consumption_order_failed", day, {"ingredient_id": 4, "quantity": 1, "location_id": "medellin_centro", "failure_code": "validation_error"})

    result = order_failure_rate_per_day(start, end)
    assert len(result) == 1
    assert result[0]["total"] == 4
    assert result[0]["failures"] == 1
    assert result[0]["failure_rate"] == 0.25


def test_date_bounds_inclusive_start_exclusive_end() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 3, tzinfo=UTC)
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
        {"location_id": "medellin_centro", "ingredient_id": 1, "quantity": 1, "reason": "consumption", "consumption_order_id": 1, "created_by": "1", "restricted_access": False},
    )
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 2, 12, tzinfo=UTC),
        {"location_id": "medellin_centro", "ingredient_id": 2, "quantity": 1, "reason": "consumption", "consumption_order_id": 2, "created_by": "1", "restricted_access": False},
    )
    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 3, 0, 0, tzinfo=UTC),
        {"location_id": "medellin_centro", "ingredient_id": 3, "quantity": 1, "reason": "consumption", "consumption_order_id": 3, "created_by": "1", "restricted_access": False},
    )

    result = consumption_by_location_per_day(start, end)
    assert sum(row["count"] for row in result) == 2


def test_auth_failure_rate_per_day() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 2, tzinfo=UTC)
    day = datetime(2026, 7, 1, 8, tzinfo=UTC)
    seed_row("user_login_succeeded", day, {"location_id": "medellin_centro"})
    seed_row("user_login_succeeded", day, {"location_id": "medellin_centro"})
    seed_row("user_login_failed", day, {"failure_reason": "wrong_credentials", "source": "backoffice", "attempt_count": 1})

    result = auth_failure_rate_per_day(start, end)
    assert len(result) == 1
    assert result[0]["total"] == 3
    assert result[0]["failures"] == 1
    assert abs(result[0]["failure_rate"] - (1 / 3)) < 1e-9


def test_metrics_are_deterministic() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 2, tzinfo=UTC)
    day = datetime(2026, 7, 1, 9, tzinfo=UTC)
    seed_row("user_login_failed", day, {"failure_reason": "wrong_credentials", "source": "backoffice", "attempt_count": 1})

    first = auth_failure_rate_per_day(start, end)
    second = auth_failure_rate_per_day(start, end)
    assert first == second
