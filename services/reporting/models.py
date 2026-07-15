"""API response / request schemas for the reporting service (CONTEXT §6 shapes)."""

from __future__ import annotations

from datetime import date
from typing import Optional

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
    run_id: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str
    week_start: Optional[str] = None
    records_extracted: int
    records_loaded: int
    missing_cost_events_count: int
    error_detail: Optional[str] = None


class TriggerPipelineRunBody(BaseModel):
    week_start: Optional[date] = None
