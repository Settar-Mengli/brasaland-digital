"""Ensure data/ is on sys.path and provide isolated SQLite fixtures for job_runs."""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Column, DateTime, Index, String, Text, event
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, create_engine

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pipelines.db_models as pipeline_db_models
import pipelines.job_runner as job_runner
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


class TelemetryEventRow(SQLModel, table=True):
    """Minimal public.telemetry_events stand-in for SQLite export tests."""

    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("ix_test_telemetry_events_timestamp", "timestamp"),
    )

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    event_type: str = Field(sa_column=Column(Text, nullable=False))
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    service: str = Field(sa_column=Column(Text, nullable=False))
    level: str = Field(sa_column=Column(Text, nullable=False))
    tags: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON))
    context: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON))


def _patch_engines() -> None:
    job_runner._engine = _test_engine
    job_runner._schema_ready = False
    pipeline_module._engine = _test_engine


def _sqlite_ready_models() -> None:
    pipeline_db_models.WeeklyLocationPerformance.__table__.schema = None
    pipeline_db_models.PipelineRun.__table__.schema = None
    pipeline_db_models.JobRun.__table__.schema = None
    for table in (
        pipeline_db_models.WeeklyLocationPerformance.__table__,
        pipeline_db_models.PipelineRun.__table__,
    ):
        for column in table.columns:
            if isinstance(column.type, PGUUID):
                column.type = String(36)


@pytest.fixture
def sqlite_db() -> Generator[None, None, None]:
    """SQLite engine with JobRun (+ optional telemetry) on the default schema."""
    _patch_engines()
    _sqlite_ready_models()

    SQLModel.metadata.create_all(
        _test_engine,
        tables=[
            pipeline_db_models.JobRun.__table__,
            TelemetryEventRow.__table__,
        ],
    )
    job_runner._schema_ready = True
    yield
    SQLModel.metadata.drop_all(
        _test_engine,
        tables=[
            pipeline_db_models.JobRun.__table__,
            TelemetryEventRow.__table__,
        ],
    )
    job_runner._schema_ready = False
    job_runner._engine = None
    pipeline_module._engine = None
    pipeline_db_models.WeeklyLocationPerformance.__table__.schema = "reporting"
    pipeline_db_models.PipelineRun.__table__.schema = "reporting"
    pipeline_db_models.JobRun.__table__.schema = "reporting"


@pytest.fixture
def seed_telemetry_row() -> Any:
    def _seed(
        *,
        event_id: str,
        event_type: str,
        timestamp: datetime,
        tags: dict[str, object] | None = None,
        context: dict[str, object] | None = None,
    ) -> None:
        with Session(_test_engine) as session:
            session.add(
                TelemetryEventRow(
                    event_id=event_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    service="backoffice",
                    level="info",
                    tags=tags or {},
                    context=context or {},
                )
            )
            session.commit()

    return _seed
