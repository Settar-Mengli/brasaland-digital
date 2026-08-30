"""HTTP routes for Celery task status."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from brasaland_auth_verify.deps import require_admin
from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from celery_app import celery_app
from models import TaskStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()

TASK_FAILED_MESSAGE = "Task failed"

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
def get_task_status(
    task_id: str,
    _admin: Annotated[str, Depends(require_admin)],
) -> TaskStatusResponse:
    async_result = AsyncResult(task_id, app=celery_app)
    state = async_result.state or "PENDING"
    status = _map_status(state)
    result: Any | None = None
    if state == "SUCCESS":
        result = async_result.result
    elif state == "FAILURE":
        logger.warning("Celery task %s failed: %s", task_id, async_result.result)
        result = TASK_FAILED_MESSAGE
    return TaskStatusResponse(task_id=task_id, status=status, result=result)
