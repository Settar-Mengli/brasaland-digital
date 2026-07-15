"""Service-facing helpers: query KPIs / run metadata and trigger the flow synchronously."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, col, select

from pipelines.db_models import PipelineRun, WeeklyLocationPerformance
from pipelines.pipeline import get_engine, weekly_location_performance_flow


def _decimal_to_number(value: Decimal | float | int) -> float:
    return float(value)


def query_weekly_location_performance(week_start: date | None = None) -> dict[str, Any]:
    """Return CONTEXT-shaped weekly location KPIs.

    When week_start is omitted, uses the most recent week_start present in
    reporting.weekly_location_performance.
    """
    engine = get_engine()
    with Session(engine) as session:
        target = week_start
        if target is None:
            latest = session.exec(
                select(WeeklyLocationPerformance.week_start)
                .order_by(col(WeeklyLocationPerformance.week_start).desc())
                .limit(1)
            ).first()
            if latest is None:
                return {"week_start": None, "locations": []}
            target = latest

        rows = session.exec(
            select(WeeklyLocationPerformance).where(
                WeeklyLocationPerformance.week_start == target
            )
        ).all()

    locations = [
        {
            "location_id": row.location_id,
            "country": row.country,
            "total_purchase_cost": _decimal_to_number(row.total_purchase_cost),
            "total_waste_cost": _decimal_to_number(row.total_waste_cost),
            "waste_ratio": _decimal_to_number(row.waste_ratio),
            "stockout_events_count": row.stockout_events_count,
            "price_alert_events_count": row.price_alert_events_count,
            "currency": row.currency,
        }
        for row in rows
    ]
    return {
        "week_start": target.isoformat() if target is not None else None,
        "locations": locations,
    }


def _run_to_dict(run: PipelineRun) -> dict[str, Any]:
    return {
        "run_id": str(run.run_id),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "week_start": run.week_start.isoformat() if run.week_start else None,
        "records_extracted": run.records_extracted,
        "records_loaded": run.records_loaded,
        "missing_cost_events_count": run.missing_cost_events_count,
        "error_detail": run.error_detail,
    }


def query_latest_pipeline_run() -> dict[str, Any]:
    """Return metadata for the most recently started pipeline run.

    When no runs exist, returns a structured empty object (all nulls) — never a
    bare null body — so clients can rely on a stable JSON shape.
    """
    empty: dict[str, Any] = {
        "run_id": None,
        "started_at": None,
        "finished_at": None,
        "status": None,
        "week_start": None,
        "records_extracted": None,
        "records_loaded": None,
        "missing_cost_events_count": None,
        "error_detail": None,
    }
    engine = get_engine()
    with Session(engine) as session:
        run = session.exec(
            select(PipelineRun).order_by(col(PipelineRun.started_at).desc()).limit(1)
        ).first()
    if run is None:
        return empty
    return _run_to_dict(run)


def trigger_pipeline_run(week_start: date | None = None) -> dict[str, Any]:
    """Run the Prefect flow synchronously and return completed pipeline_runs metadata.

    Blocks until the flow finishes. Callers should treat long weeks as request-blocking;
    an async/queued trigger is a deliberate follow-up, not implemented here.
    """
    summary = weekly_location_performance_flow(week_start=week_start)
    run_id = summary.get("run_id")
    if not run_id:
        return summary

    engine = get_engine()
    with Session(engine) as session:
        run = session.get(PipelineRun, UUID(str(run_id)))
    if run is None:
        return summary
    return _run_to_dict(run)
