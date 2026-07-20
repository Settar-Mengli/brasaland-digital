"""HTTP routes for Celery task status."""

from __future__ import annotations

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter

from celery_app import celery_app
from models import TaskStatusResponse

router = APIRouter()

_STATE_MAP = {
    "PENDING": "pending",
    "STARTED": "started",
    "SUCCESS": "success",
    "FAILURE": "failure",
    "RETRY": "pending",
    "REVOKED": "failure",
}


def _map_status(celery_state: str) -> str:
    return _STATE_MAP.get(celery_state, celery_state.lower())


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    async_result = AsyncResult(task_id, app=celery_app)
    state = async_result.state or "PENDING"
    status = _map_status(state)
    result: Any | None = None
    if state == "SUCCESS":
        result = async_result.result
    elif state == "FAILURE":
        result = str(async_result.result) if async_result.result is not None else None
    return TaskStatusResponse(task_id=task_id, status=status, result=result)
