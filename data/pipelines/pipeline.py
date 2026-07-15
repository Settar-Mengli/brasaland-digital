"""Prefect flow: weekly location performance ETL over telemetry_events (read-only)."""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from dotenv import load_dotenv
from prefect import flow, task
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine, select

from pipelines.db_models import PipelineRun
from pipelines.locations import LOCATION_DIMENSIONS, PRICE_ALERT_BASELINE_WEEKS
from pipelines.transform import LocationWeekRow, transform_week

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def most_recent_complete_iso_week(today: date | None = None) -> date:
    """Return Monday (UTC) of the most recent ISO week that has fully ended."""
    today = today or datetime.now(timezone.utc).date()
    ref = today - timedelta(days=7)
    return ref - timedelta(days=ref.weekday())


def get_engine() -> Engine:
    """Lazy engine so importing this module never opens a database connection."""
    global _engine
    if _engine is not None:
        return _engine

    url = os.environ.get("DATABASE_URL")
    if not url:
        load_dotenv()
        url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")

    _engine = create_engine(url, echo=False)
    return _engine


def _week_bounds(week_start: date) -> tuple[datetime, datetime]:
    start = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=7)


def _lookback_start(week_start: date) -> datetime:
    start, _ = _week_bounds(week_start)
    return start - timedelta(weeks=PRICE_ALERT_BASELINE_WEEKS)


def _row_to_record(row: Any) -> dict[str, Any]:
    return {
        "event_id": row.event_id,
        "event_type": row.event_type,
        "timestamp": row.timestamp,
        "tags": row.tags if isinstance(row.tags, dict) else (row.tags or {}),
        "context": row.context if isinstance(row.context, dict) else (row.context or {}),
    }


def transform_cache_key_fn(context: Any, parameters: dict[str, Any]) -> str:
    """Cache key = week_start + record count + sha256 of sorted event_ids.

    Validity window: cache_expiration=1 hour — same extract snapshot reuses the
    KPI transform within an hour; after that stale transforms are recomputed.
    Key uses '-' separators only (Windows-safe; no ':', '/', or '\\').
    """
    week_start = parameters["week_start"]
    records = parameters["records"]
    event_ids = sorted(str(r.get("event_id", "")) for r in records)
    digest = hashlib.sha256("|".join(event_ids).encode("utf-8")).hexdigest()[:16]
    # Windows-safe: no ':', '/', or '\' — Prefect persists cache keys as path segments.
    return f"transform_kpis-{week_start}-n={len(records)}-{digest}"


# Retries=3 / delay=10s: extract talks to Postgres; transient network blips and
# brief pool saturation are expected against Supabase and should not fail the run.
@task(retries=3, retry_delay_seconds=10)
def extract_week(week_start: date) -> list[dict[str, Any]]:
    """Read telemetry_events for the target week plus supply lookback (read-only)."""
    week_start_dt, week_end_dt = _week_bounds(week_start)
    lookback_dt = _lookback_start(week_start)
    engine = get_engine()
    sql = text(
        """
        SELECT event_id, event_type, timestamp, tags, context
        FROM public.telemetry_events
        WHERE (
            timestamp >= :week_start AND timestamp < :week_end
            AND event_type IN (
                'supply_order_created',
                'consumption_order_created',
                'stock_threshold_triggered'
            )
        ) OR (
            event_type = 'supply_order_created'
            AND timestamp >= :lookback_start AND timestamp < :week_end
        )
        ORDER BY timestamp ASC
        """
    )
    with engine.connect() as conn:
        result = conn.execute(
            sql,
            {
                "week_start": week_start_dt,
                "week_end": week_end_dt,
                "lookback_start": lookback_dt,
            },
        )
        rows = result.fetchall()
    records = [_row_to_record(row) for row in rows]
    logger.info("extract_week week_start=%s records=%s", week_start, len(records))
    return records


@task(
    cache_key_fn=transform_cache_key_fn,
    cache_expiration=timedelta(hours=1),
)
def transform_kpis(week_start: date, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate five CONTEXT KPIs into 14 location rows for the ISO week."""
    result = transform_week(records, week_start)
    return {
        "missing_cost_events_count": result.missing_cost_events_count,
        "rows": [
            {
                "location_id": row.location_id,
                "country": row.country,
                "week_start": row.week_start.isoformat(),
                "total_purchase_cost": str(row.total_purchase_cost),
                "total_waste_cost": str(row.total_waste_cost),
                "waste_ratio": str(row.waste_ratio),
                "stockout_events_count": row.stockout_events_count,
                "price_alert_events_count": row.price_alert_events_count,
                "currency": row.currency,
            }
            for row in result.rows
        ],
    }


def _rows_from_payload(payload: dict[str, Any]) -> list[LocationWeekRow]:
    rows: list[LocationWeekRow] = []
    for item in payload["rows"]:
        rows.append(
            LocationWeekRow(
                location_id=item["location_id"],
                country=item["country"],
                week_start=date.fromisoformat(item["week_start"]),
                total_purchase_cost=Decimal(item["total_purchase_cost"]),
                total_waste_cost=Decimal(item["total_waste_cost"]),
                waste_ratio=Decimal(item["waste_ratio"]),
                stockout_events_count=int(item["stockout_events_count"]),
                price_alert_events_count=int(item["price_alert_events_count"]),
                currency=item["currency"],
            )
        )
    return rows


# Retries=3 / delay=10s: load upserts into Postgres; connection drops mid-batch
# should retry rather than leave a Failed run without a second attempt.
@task(retries=3, retry_delay_seconds=10)
def load_weekly_performance(
    week_start: date,
    transform_payload: dict[str, Any],
) -> int:
    """Upsert KPI rows on unique(location_id, week_start)."""
    rows = _rows_from_payload(transform_payload)
    engine = get_engine()
    now = datetime.now(timezone.utc)
    loaded = 0
    upsert_sql = text(
        """
        INSERT INTO reporting.weekly_location_performance (
            id, location_id, country, week_start,
            total_purchase_cost, total_waste_cost, waste_ratio,
            stockout_events_count, price_alert_events_count,
            currency, computed_at
        ) VALUES (
            :id, :location_id, :country, :week_start,
            :total_purchase_cost, :total_waste_cost, :waste_ratio,
            :stockout_events_count, :price_alert_events_count,
            :currency, :computed_at
        )
        ON CONFLICT (location_id, week_start) DO UPDATE SET
            country = EXCLUDED.country,
            total_purchase_cost = EXCLUDED.total_purchase_cost,
            total_waste_cost = EXCLUDED.total_waste_cost,
            waste_ratio = EXCLUDED.waste_ratio,
            stockout_events_count = EXCLUDED.stockout_events_count,
            price_alert_events_count = EXCLUDED.price_alert_events_count,
            currency = EXCLUDED.currency,
            computed_at = EXCLUDED.computed_at
        """
    )
    with engine.begin() as conn:
        for row in rows:
            conn.execute(
                upsert_sql,
                {
                    "id": str(uuid4()),
                    "location_id": row.location_id,
                    "country": row.country,
                    "week_start": week_start,
                    "total_purchase_cost": row.total_purchase_cost,
                    "total_waste_cost": row.total_waste_cost,
                    "waste_ratio": row.waste_ratio,
                    "stockout_events_count": row.stockout_events_count,
                    "price_alert_events_count": row.price_alert_events_count,
                    "currency": row.currency,
                    "computed_at": now,
                },
            )
            loaded += 1
    return loaded


# Retries=3 / delay=10s: pipeline_runs writes are external Postgres touches.
@task(retries=3, retry_delay_seconds=10)
def write_pipeline_run_start(week_start: date) -> str:
    """Insert a Running pipeline_runs row; enforce one Running row per week_start."""
    engine = get_engine()
    run_id = uuid4()
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        existing = session.exec(
            select(PipelineRun).where(
                PipelineRun.week_start == week_start,
                PipelineRun.status == "Running",
            )
        ).first()
        if existing is not None:
            raise RuntimeError(
                f"Concurrent run already Running for week_start={week_start} "
                f"(run_id={existing.run_id})"
            )
        session.add(
            PipelineRun(
                run_id=run_id,
                started_at=now,
                finished_at=None,
                status="Running",
                week_start=week_start,
                records_extracted=0,
                records_loaded=0,
                missing_cost_events_count=0,
                error_detail=None,
            )
        )
        session.commit()
    return str(run_id)


# Retries=3 / delay=10s: finishing the run log must survive brief DB blips.
@task(retries=3, retry_delay_seconds=10)
def write_pipeline_run_finish(
    run_id: str,
    status: str,
    records_extracted: int,
    records_loaded: int,
    missing_cost_events_count: int,
    error_detail: str | None = None,
) -> None:
    """Update terminal status and counts on the pipeline_runs row."""
    engine = get_engine()
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        run = session.get(PipelineRun, UUID(run_id))
        if run is None:
            raise RuntimeError(f"pipeline_runs row not found: {run_id}")
        run.status = status
        run.finished_at = now
        run.records_extracted = records_extracted
        run.records_loaded = records_loaded
        run.missing_cost_events_count = missing_cost_events_count
        run.error_detail = error_detail
        session.add(run)
        session.commit()


@task
def notify_run_summary(summary: dict[str, Any]) -> None:
    """Optional console notification of run outcome (observability only)."""
    logger.info(
        "pipeline run summary run_id=%s status=%s week_start=%s "
        "extracted=%s loaded=%s missing_cost=%s",
        summary.get("run_id"),
        summary.get("status"),
        summary.get("week_start"),
        summary.get("records_extracted"),
        summary.get("records_loaded"),
        summary.get("missing_cost_events_count"),
    )
    print(
        f"[reporting-pipeline] run_id={summary.get('run_id')} "
        f"status={summary.get('status')} week_start={summary.get('week_start')} "
        f"extracted={summary.get('records_extracted')} "
        f"loaded={summary.get('records_loaded')} "
        f"missing_cost={summary.get('missing_cost_events_count')}"
    )


@flow(name="extract_weekly_telemetry")
def extract_weekly_telemetry(week_start: date) -> list[dict[str, Any]]:
    """Subflow: read telemetry_events for the target week plus supply lookback."""
    return extract_week(week_start)


@flow(name="compute_weekly_kpis")
def compute_weekly_kpis(
    week_start: date,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Subflow: aggregate five CONTEXT KPIs into location-week rows."""
    return transform_kpis(week_start, records)


@flow(name="load_weekly_performance_report")
def load_weekly_performance_report(
    week_start: date,
    payload: dict[str, Any],
) -> int:
    """Subflow: upsert KPI rows into reporting.weekly_location_performance."""
    return load_weekly_performance(week_start, payload)


@flow(name="weekly_location_performance_flow")
def weekly_location_performance_flow(week_start: date | None = None) -> dict[str, Any]:
    """Extract → transform → load weekly KPIs via domain subflows; record pipeline_runs."""
    target_week = week_start or most_recent_complete_iso_week()
    run_id = write_pipeline_run_start(target_week)
    records_extracted = 0
    records_loaded = 0
    missing_cost = 0
    status = "Completed"
    error_detail: str | None = None

    try:
        records = extract_weekly_telemetry(target_week)
        records_extracted = len(records)
        transform_payload = compute_weekly_kpis(target_week, records)
        missing_cost = int(transform_payload["missing_cost_events_count"])
        records_loaded = load_weekly_performance_report(target_week, transform_payload)
        write_pipeline_run_finish(
            run_id,
            status="Completed",
            records_extracted=records_extracted,
            records_loaded=records_loaded,
            missing_cost_events_count=missing_cost,
            error_detail=None,
        )
    except Exception as exc:  # noqa: BLE001 — flow must mark Failed then re-raise
        status = "Failed"
        error_detail = f"{type(exc).__name__}: {exc}"
        try:
            write_pipeline_run_finish(
                run_id,
                status="Failed",
                records_extracted=records_extracted,
                records_loaded=records_loaded,
                missing_cost_events_count=missing_cost,
                error_detail=error_detail,
            )
        except Exception:  # noqa: BLE001
            logger.exception("failed to write Failed pipeline_runs row")
        raise

    summary = {
        "run_id": run_id,
        "status": status,
        "week_start": target_week.isoformat(),
        "records_extracted": records_extracted,
        "records_loaded": records_loaded,
        "missing_cost_events_count": missing_cost,
        "error_detail": error_detail,
        "location_count": len(LOCATION_DIMENSIONS),
    }
    # Optional observability only — flow continues if notify fails.
    notify_state = notify_run_summary(summary, return_state=True)
    if notify_state is not None and notify_state.is_failed():
        logger.warning("notify_run_summary failed; flow continuing with Completed load")

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = weekly_location_performance_flow()
    print(result)
