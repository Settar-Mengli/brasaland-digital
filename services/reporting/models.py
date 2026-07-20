"""API response / request schemas for the reporting service (CONTEXT §6 shapes)."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class LocationPerformanceItem(BaseModel):
    location_id: str
    country: str
    total_purchase_cost: float
    total_waste_cost: float
    waste_ratio: float
    stockout_events_count: int
    price_alert_events_count: int
    currency: str


class WeeklyLocationPerformanceResponse(BaseModel):
    week_start: Optional[str] = None
    locations: list[LocationPerformanceItem] = Field(default_factory=list)


class PipelineRunResponse(BaseModel):
    run_id: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: Optional[str] = None
    week_start: Optional[str] = None
    records_extracted: Optional[int] = None
    records_loaded: Optional[int] = None
    missing_cost_events_count: Optional[int] = None
    error_detail: Optional[str] = None


class TriggerPipelineRunBody(BaseModel):
    week_start: Optional[date] = None


class TaskAcceptedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None
