"""GET /tasks/{task_id} status mapping (AsyncResult mocked; no Redis)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("celery_state", "expected_status", "result", "expected_result"),
    [
        ("PENDING", "pending", None, None),
        ("STARTED", "started", None, None),
        ("SUCCESS", "success", {"run_id": "r1", "status": "Completed"}, {"run_id": "r1", "status": "Completed"}),
        ("FAILURE", "failure", RuntimeError("boom"), "Task failed"),
    ],
)
async def test_get_task_status_maps_states(
    asgi_client: httpx.AsyncClient,
    celery_state: str,
    expected_status: str,
    result: object,
    expected_result: object,
) -> None:
    mock_result = MagicMock()
    mock_result.state = celery_state
    mock_result.result = result

    with patch("routers.tasks.AsyncResult", return_value=mock_result):
        response = await asgi_client.get("/tasks/task-123")

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-123"
    assert body["status"] == expected_status
    assert body["result"] == expected_result
