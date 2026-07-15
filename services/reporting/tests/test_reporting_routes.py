"""Router-boundary HTTP shape tests (pipelines.api stubbed; httpx ASGI)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import httpx
import pytest


SAMPLE_WEEKLY_PAYLOAD = {
    "week_start": "2026-07-07",
    "locations": [
        {
            "location_id": "medellin_centro",
            "country": "CO",
            "total_purchase_cost": 8420000.0,
            "total_waste_cost": 610000.0,
            "waste_ratio": 0.072,
            "stockout_events_count": 2,
            "price_alert_events_count": 1,
            "currency": "COP",
        }
    ],
}

SAMPLE_RUN_PAYLOAD = {
    "run_id": "11111111-1111-1111-1111-111111111111",
    "started_at": "2026-07-14T00:00:00+00:00",
    "finished_at": "2026-07-14T00:05:00+00:00",
    "status": "Completed",
    "week_start": "2026-07-07",
    "records_extracted": 120,
    "records_loaded": 14,
    "missing_cost_events_count": 3,
    "error_detail": None,
}

LOCATION_FIELDS = (
    "location_id",
    "country",
    "total_purchase_cost",
    "total_waste_cost",
    "waste_ratio",
    "stockout_events_count",
    "price_alert_events_count",
    "currency",
)


@pytest.mark.anyio
async def test_get_weekly_location_performance_shape(asgi_client: httpx.AsyncClient) -> None:
    with patch(
        "routers.reporting.query_weekly_location_performance",
        return_value=SAMPLE_WEEKLY_PAYLOAD,
    ):
        response = await asgi_client.get("/reporting/weekly-location-performance")

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-07-07"
    assert isinstance(body["locations"], list)
    assert len(body["locations"]) == 1
    location = body["locations"][0]
    for field in LOCATION_FIELDS:
        assert field in location


@pytest.mark.anyio
async def test_get_weekly_location_performance_passes_week_start(
    asgi_client: httpx.AsyncClient,
) -> None:
    with patch(
        "routers.reporting.query_weekly_location_performance",
        return_value=SAMPLE_WEEKLY_PAYLOAD,
    ) as mock_query:
        response = await asgi_client.get(
            "/reporting/weekly-location-performance",
            params={"week_start": "2026-07-07"},
        )

    assert response.status_code == 200
    mock_query.assert_called_once_with(week_start=date(2026, 7, 7))


@pytest.mark.anyio
async def test_get_latest_pipeline_run_shape(asgi_client: httpx.AsyncClient) -> None:
    with patch(
        "routers.reporting.query_latest_pipeline_run",
        return_value=SAMPLE_RUN_PAYLOAD,
    ):
        response = await asgi_client.get("/reporting/pipeline-runs/latest")

    assert response.status_code == 200
    body = response.json()
    for field in (
        "run_id",
        "started_at",
        "finished_at",
        "status",
        "week_start",
        "records_extracted",
        "records_loaded",
        "missing_cost_events_count",
        "error_detail",
    ):
        assert field in body
    assert body["status"] == "Completed"


@pytest.mark.anyio
async def test_post_pipeline_runs_returns_completed_metadata(
    asgi_client: httpx.AsyncClient,
) -> None:
    with patch(
        "routers.reporting.trigger_pipeline_run",
        return_value=SAMPLE_RUN_PAYLOAD,
    ) as mock_trigger:
        response = await asgi_client.post("/reporting/pipeline-runs")

    assert response.status_code == 200
    mock_trigger.assert_called_once_with(week_start=None)
    body = response.json()
    assert body["run_id"] == SAMPLE_RUN_PAYLOAD["run_id"]
    assert body["status"] == "Completed"
    assert body["records_loaded"] == 14


@pytest.mark.anyio
async def test_get_weekly_location_performance_empty_state(
    asgi_client: httpx.AsyncClient,
) -> None:
    with patch(
        "routers.reporting.query_weekly_location_performance",
        return_value={"week_start": None, "locations": []},
    ):
        response = await asgi_client.get("/reporting/weekly-location-performance")

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] is None
    assert body["locations"] == []
