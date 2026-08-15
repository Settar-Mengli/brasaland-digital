from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport


@pytest.mark.anyio
async def test_enqueue_and_task_status_require_token() -> None:
    from app import app

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        assert (await client.post("/reporting/pipeline-runs")).status_code == 401
        assert (await client.get("/tasks/task-123")).status_code == 401


@pytest.mark.anyio
async def test_reporting_reads_remain_public() -> None:
    from app import app
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        with patch(
            "routers.reporting.query_weekly_location_performance",
            return_value={"week_start": None, "locations": []},
        ):
            assert (
                await client.get("/reporting/weekly-location-performance")
            ).status_code == 200
