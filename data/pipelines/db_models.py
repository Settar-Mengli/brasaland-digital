"""SQLModel tables for reporting.weekly_location_performance and reporting.pipeline_runs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Field, SQLModel


class WeeklyLocationPerformance(SQLModel, table=True):
    """One KPI row per location per ISO week (CONTEXT destination DDL)."""

    __tablename__ = "weekly_location_performance"
    __table_args__ = (
        UniqueConstraint("location_id", "week_start", name="uq_weekly_location_week"),
        {"schema": "reporting"},
    )

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    location_id: str = Field(sa_column=Column(Text, nullable=False))
    country: str = Field(sa_column=Column(Text, nullable=False))
    week_start: date = Field(nullable=False)
    total_purchase_cost: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric, nullable=False, server_default="0"),
    )
    total_waste_cost: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric, nullable=False, server_default="0"),
    )
    waste_ratio: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric, nullable=False, server_default="0"),
    )
    stockout_events_count: int = Field(default=0, nullable=False)
    price_alert_events_count: int = Field(default=0, nullable=False)
    currency: str = Field(sa_column=Column(Text, nullable=False))
    computed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class PipelineRun(SQLModel, table=True):
    """Execution log for one weekly_location_performance flow attempt (design §7)."""

    __tablename__ = "pipeline_runs"
    __table_args__ = ({"schema": "reporting"},)

    run_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    status: str = Field(sa_column=Column(Text, nullable=False))
    week_start: date = Field(nullable=False)
    records_extracted: int = Field(default=0, nullable=False)
    records_loaded: int = Field(default=0, nullable=False)
    missing_cost_events_count: int = Field(default=0, nullable=False)
    error_detail: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )


class JobRun(SQLModel, table=True):
    """Nightly orchestration state for one (job_name, target_date)."""

    __tablename__ = "job_runs"
    __table_args__ = (
        UniqueConstraint("job_name", "target_date", name="uq_job_runs_job_date"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_job_runs_status",
        ),
        {"schema": "reporting"},
    )

    id: int | None = Field(default=None, primary_key=True)
    job_name: str = Field(sa_column=Column(Text, nullable=False))
    target_date: date = Field(nullable=False)
    status: str = Field(sa_column=Column(Text, nullable=False))
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class TaskDeadLetter(SQLModel, table=True):
    """Celery task failures after retry exhaustion (DEV-55 DLQ)."""

    __tablename__ = "task_dead_letters"
    __table_args__ = ({"schema": "reporting"},)

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(sa_column=Column(Text, nullable=False))
    task_name: str = Field(sa_column=Column(Text, nullable=False))
    attempt_count: int = Field(nullable=False)
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
