"""HTTP routes for weekly location performance and pipeline run control."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from models import (
    PipelineRunResponse,
    TaskAcceptedResponse,
    TriggerPipelineRunBody,
    WeeklyLocationPerformanceResponse,
)
from pipelines.api import (
    query_latest_pipeline_run,
    query_weekly_location_performance,
)
from tasks import run_pipeline_task

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


@router.post(
    "/pipeline-runs",
    response_model=TaskAcceptedResponse,
    status_code=202,
)
def post_pipeline_run(body: TriggerPipelineRunBody | None = None) -> JSONResponse:
    week_start = body.week_start if body is not None else None
    week_arg = week_start.isoformat() if week_start is not None else None
    async_result = run_pipeline_task.delay(week_arg)
    return JSONResponse(
        status_code=202,
        content={"task_id": async_result.id},
    )
