"""HTTP routes for weekly location performance and pipeline run control."""

from datetime import date
from typing import Annotated

from brasaland_auth_verify.deps import require_admin
from fastapi import APIRouter, Body, Depends, Query, Request
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
from rate_limit import ENQUEUE_RATE_LIMIT, limiter
from tasks import run_pipeline_task

router = APIRouter(prefix="/reporting")


@router.get(
    "/weekly-location-performance",
    response_model=WeeklyLocationPerformanceResponse,
)
def get_weekly_location_performance(
    _admin: Annotated[str, Depends(require_admin)],
    week_start: date | None = Query(default=None),
) -> WeeklyLocationPerformanceResponse:
    payload = query_weekly_location_performance(week_start=week_start)
    return WeeklyLocationPerformanceResponse.model_validate(payload)


@router.get("/pipeline-runs/latest", response_model=PipelineRunResponse)
def get_latest_pipeline_run(
    _admin: Annotated[str, Depends(require_admin)],
) -> PipelineRunResponse:
    payload = query_latest_pipeline_run()
    return PipelineRunResponse.model_validate(payload)


@router.post(
    "/pipeline-runs",
    response_model=TaskAcceptedResponse,
    status_code=202,
)
@limiter.limit(ENQUEUE_RATE_LIMIT)
def post_pipeline_run(
    request: Request,
    _admin: Annotated[str, Depends(require_admin)],
    body: Annotated[TriggerPipelineRunBody | None, Body()] = None,
) -> JSONResponse:
    week_start = body.week_start if body is not None else None
    week_arg = week_start.isoformat() if week_start is not None else None
    async_result = run_pipeline_task.delay(week_arg)
    return JSONResponse(
        status_code=202,
        content={"task_id": async_result.id},
    )
