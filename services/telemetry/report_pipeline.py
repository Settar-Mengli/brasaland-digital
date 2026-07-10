from __future__ import annotations

from datetime import datetime

from analysis import (
    auth_failure_rate_per_day,
    consumption_by_location_per_day,
    order_failure_rate_per_day,
)


def run_report_pipeline(start_date: datetime, end_date: datetime) -> dict[str, list[dict]]:
    return {
        "consumption_by_location_per_day": consumption_by_location_per_day(start_date, end_date),
        "order_failure_rate_per_day": order_failure_rate_per_day(start_date, end_date),
        "auth_failure_rate_per_day": auth_failure_rate_per_day(start_date, end_date),
    }
