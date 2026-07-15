"""SQLite ensure_schema + upsert idempotency (no live DB)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import database
from pipelines.db_models import WeeklyLocationPerformance
from sqlmodel import Session, select

from conftest import upsert_weekly_location_row


def test_upsert_idempotent_same_location_week(sqlite_db: None) -> None:
    week_start = date(2026, 7, 7)
    upsert_weekly_location_row(
        location_id="medellin_centro",
        country="CO",
        week_start=week_start,
        total_purchase_cost=Decimal("1000"),
        total_waste_cost=Decimal("50"),
        waste_ratio=Decimal("0.05"),
        stockout_events_count=1,
        price_alert_events_count=0,
        currency="COP",
    )
    upsert_weekly_location_row(
        location_id="medellin_centro",
        country="CO",
        week_start=week_start,
        total_purchase_cost=Decimal("2000"),
        total_waste_cost=Decimal("100"),
        waste_ratio=Decimal("0.05"),
        stockout_events_count=3,
        price_alert_events_count=2,
        currency="COP",
    )

    with Session(database.get_engine()) as session:
        rows = session.exec(select(WeeklyLocationPerformance)).all()

    assert len(rows) == 1
    row = rows[0]
    assert row.location_id == "medellin_centro"
    assert row.week_start == week_start
    assert row.total_purchase_cost == Decimal("2000")
    assert row.total_waste_cost == Decimal("100")
    assert row.stockout_events_count == 3
    assert row.price_alert_events_count == 2
