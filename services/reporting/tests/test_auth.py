from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport


@pytest.mark.anyio
async def test_all_reporting_routes_require_token() -> None:
    from app import app

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        assert (await client.get("/reporting/weekly-location-performance")).status_code == 401
        assert (await client.get("/reporting/pipeline-runs/latest")).status_code == 401
        assert (await client.post("/reporting/pipeline-runs")).status_code == 401
        assert (await client.get("/tasks/task-123")).status_code == 401


@pytest.mark.anyio
async def test_non_admin_is_forbidden_from_all_reporting_routes(
    non_admin_token: str,
) -> None:
    from app import app

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {non_admin_token}"},
    ) as client:
        assert (await client.get("/reporting/weekly-location-performance")).status_code == 403
        assert (await client.get("/reporting/pipeline-runs/latest")).status_code == 403
        assert (await client.post("/reporting/pipeline-runs")).status_code == 403
        assert (await client.get("/tasks/task-123")).status_code == 403


@pytest.mark.anyio
async def test_admin_can_access_all_reporting_routes(
    asgi_client: httpx.AsyncClient,
) -> None:
    async_result = MagicMock()
    async_result.id = "task-123"
    task_status = MagicMock()
    task_status.state = "PENDING"
    task_status.result = None

    with (
        patch(
            "routers.reporting.query_weekly_location_performance",
            return_value={"week_start": None, "locations": []},
        ),
        patch(
            "routers.reporting.query_latest_pipeline_run",
            return_value={
                "run_id": None,
                "started_at": None,
                "finished_at": None,
                "status": None,
                "week_start": None,
                "records_extracted": None,
                "records_loaded": None,
                "missing_cost_events_count": None,
                "error_detail": None,
            },
        ),
        patch("routers.reporting.run_pipeline_task.delay", return_value=async_result),
        patch("routers.tasks.AsyncResult", return_value=task_status),
    ):
        assert (await asgi_client.get("/reporting/weekly-location-performance")).status_code == 200
        assert (await asgi_client.get("/reporting/pipeline-runs/latest")).status_code == 200
        assert (await asgi_client.post("/reporting/pipeline-runs")).status_code == 202
        assert (await asgi_client.get("/tasks/task-123")).status_code == 200
