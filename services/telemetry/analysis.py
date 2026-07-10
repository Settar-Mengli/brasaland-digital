from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy import select

import database
from db_models import TelemetryEventRow


def _load_events_df(
    event_types: tuple[str, ...],
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
    database.ensure_schema()
    statement = (
        select(
            TelemetryEventRow.id,
            TelemetryEventRow.event_type,
            TelemetryEventRow.timestamp,
            TelemetryEventRow.tags,
        )
        .where(TelemetryEventRow.event_type.in_(event_types))
        .where(TelemetryEventRow.timestamp >= start_date)
        .where(TelemetryEventRow.timestamp < end_date)
    )
    with database.engine.connect() as connection:
        frame = pd.read_sql(statement, connection)
    if frame.empty:
        return frame
    frame["tags"] = _normalize_tags(frame["tags"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["date"] = frame["timestamp"].dt.date
    return frame


def _normalize_tags(series: pd.Series) -> pd.Series:
    def parse_tag(value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    return series.map(parse_tag)


def _json_safe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = frame.reset_index(drop=True).to_dict(orient="records")
    safe: list[dict[str, Any]] = []
    for record in records:
        safe.append(_json_safe_record(record))
    return safe


def _json_safe_record(record: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, date):
            converted[key] = value.isoformat()
        elif hasattr(value, "item"):
            converted[key] = value.item()
        else:
            converted[key] = value
    return converted


def consumption_by_location_per_day(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    frame = _load_events_df(("consumption_order_created",), start_date, end_date)
    if frame.empty:
        return []

    frame["location_id"] = frame["tags"].map(lambda tags: tags.get("location_id"))
    frame = frame.dropna(subset=["location_id"])
    if frame.empty:
        return []

    grouped = (
        frame.groupby(["date", "location_id"], as_index=False)["id"]
        .count()
        .rename(columns={"id": "count"})
    )
    return _json_safe_records(grouped)


def order_failure_rate_per_day(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    event_types = (
        "supply_order_created",
        "consumption_order_created",
        "supply_order_failed",
        "consumption_order_failed",
    )
    frame = _load_events_df(event_types, start_date, end_date)
    if frame.empty:
        return []

    frame["is_failure"] = frame["event_type"].str.endswith("_failed")
    grouped = frame.groupby("date", as_index=False).agg(
        total=("id", "count"),
        failures=("is_failure", "sum"),
    )
    grouped["failure_rate"] = grouped["failures"] / grouped["total"]
    return _json_safe_records(grouped)


def auth_failure_rate_per_day(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    frame = _load_events_df(("user_login_succeeded", "user_login_failed"), start_date, end_date)
    if frame.empty:
        return []

    frame["is_failure"] = frame["event_type"] == "user_login_failed"
    grouped = frame.groupby("date", as_index=False).agg(
        total=("id", "count"),
        failures=("is_failure", "sum"),
    )
    grouped["failure_rate"] = grouped["failures"] / grouped["total"]
    return _json_safe_records(grouped)
