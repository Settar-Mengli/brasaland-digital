"""Shared fixtures for reporting service tests (SQLite in-memory only)."""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import String, event, inspect, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite://")

import config  # noqa: F401 — data/ on sys.path
import database
import pipelines.db_models as pipeline_db_models
import pipelines.pipeline as pipeline_module

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _patch_engines() -> None:
    database._engine = _test_engine
    database._schema_ready = False
    pipeline_module._engine = _test_engine


def _sqlite_ready_models() -> None:
    pipeline_db_models.WeeklyLocationPerformance.__table__.schema = None
    pipeline_db_models.PipelineRun.__table__.schema = None
    for table in (
        pipeline_db_models.WeeklyLocationPerformance.__table__,
        pipeline_db_models.PipelineRun.__table__,
    ):
        for column in table.columns:
            if isinstance(column.type, PGUUID):
                column.type = String(36)


@pytest.fixture
def sqlite_db() -> Generator[None, None, None]:
    """SQLite engine with reporting models on the default schema (no live DB)."""
    _patch_engines()
    _sqlite_ready_models()

    SQLModel.metadata.create_all(
        _test_engine,
        tables=[
            pipeline_db_models.WeeklyLocationPerformance.__table__,
            pipeline_db_models.PipelineRun.__table__,
        ],
    )
    database._schema_ready = True
    table_names = inspect(_test_engine).get_table_names()
    assert "weekly_location_performance" in table_names
    yield
    SQLModel.metadata.drop_all(
        _test_engine,
        tables=[
            pipeline_db_models.WeeklyLocationPerformance.__table__,
            pipeline_db_models.PipelineRun.__table__,
        ],
    )
    database._schema_ready = False
    pipeline_db_models.WeeklyLocationPerformance.__table__.schema = "reporting"
    pipeline_db_models.PipelineRun.__table__.schema = "reporting"


@pytest.fixture
async def asgi_client() -> httpx.AsyncClient:
    from app import app

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def upsert_weekly_location_row(
    *,
    location_id: str,
    country: str,
    week_start: date,
    total_purchase_cost: Decimal,
    total_waste_cost: Decimal,
    waste_ratio: Decimal,
    stockout_events_count: int,
    price_alert_events_count: int,
    currency: str,
) -> None:
    """Mirror pipeline load upsert semantics for SQLite (unqualified table name)."""
    upsert_sql = text(
        """
        INSERT INTO weekly_location_performance (
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
            country = excluded.country,
            total_purchase_cost = excluded.total_purchase_cost,
            total_waste_cost = excluded.total_waste_cost,
            waste_ratio = excluded.waste_ratio,
            stockout_events_count = excluded.stockout_events_count,
            price_alert_events_count = excluded.price_alert_events_count,
            currency = excluded.currency,
            computed_at = excluded.computed_at
        """
    )
    with database.get_engine().begin() as conn:
        conn.execute(
            upsert_sql,
            {
                "id": str(uuid4()),
                "location_id": location_id,
                "country": country,
                "week_start": week_start,
                "total_purchase_cost": float(total_purchase_cost),
                "total_waste_cost": float(total_waste_cost),
                "waste_ratio": float(waste_ratio),
                "stockout_events_count": stockout_events_count,
                "price_alert_events_count": price_alert_events_count,
                "currency": currency,
                "computed_at": datetime.now(timezone.utc),
            },
        )
