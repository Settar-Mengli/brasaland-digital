"""HTTP routes for weekly location performance and pipeline run control."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from models import (
    PipelineRunResponse,
    TriggerPipelineRunBody,
    WeeklyLocationPerformanceResponse,
)
from pipelines.api import (
    query_latest_pipeline_run,
    query_weekly_location_performance,
    trigger_pipeline_run,
)

router = APIRouter(prefix="/reporting")


@router.get(
    "/weekly-location-performance",
    response_model=WeeklyLocationPerformanceResponse,
)
def get_weekly_location_performance(
    week_start: date | None = Query(default=None),
) -> WeeklyLocationPerformanceResponse:
    payload = query_weekly_location_performance(week_start=week_start)
    return WeeklyLocationPerformanceResponse.model_validate(payload)


@router.get("/pipeline-runs/latest", response_model=PipelineRunResponse)
def get_latest_pipeline_run() -> PipelineRunResponse:
    payload = query_latest_pipeline_run()
    return PipelineRunResponse.model_validate(payload)


@router.post("/pipeline-runs", response_model=PipelineRunResponse)
def post_pipeline_run(body: TriggerPipelineRunBody | None = None) -> PipelineRunResponse:
    week_start = body.week_start if body is not None else None
    payload = trigger_pipeline_run(week_start=week_start)
    return PipelineRunResponse.model_validate(payload)
