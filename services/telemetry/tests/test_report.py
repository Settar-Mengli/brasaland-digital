from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from report_service import get_report_payload


def _sample_metrics() -> dict[str, list[dict]]:
    return {
        "consumption_by_location_per_day": [{"date": "2026-07-01", "location_id": "medellin_centro", "count": 1}],
        "order_failure_rate_per_day": [{"date": "2026-07-01", "total": 1, "failures": 0, "failure_rate": 0.0}],
        "auth_failure_rate_per_day": [{"date": "2026-07-01", "total": 1, "failures": 0, "failure_rate": 0.0}],
    }


def test_report_default_period_200_structure(client) -> None:
    response = client.get("/telemetry/report")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"period", "metrics"}
    assert set(body["period"].keys()) == {"from", "to"}
    assert set(body["metrics"].keys()) == {
        "consumption_by_location_per_day",
        "order_failure_rate_per_day",
        "auth_failure_rate_per_day",
    }


def test_report_explicit_dates_honored(client) -> None:
    from tests.conftest import seed_row

    seed_row(
        "consumption_order_created",
        datetime(2026, 7, 5, 12, tzinfo=UTC),
        {
            "location_id": "medellin_centro",
            "ingredient_id": 1,
            "quantity": 1,
            "reason": "consumption",
            "consumption_order_id": 1,
            "created_by": "1",
            "restricted_access": False,
        },
    )

    response = client.get(
        "/telemetry/report",
        params={"start_date": "2026-07-05T00:00:00Z", "end_date": "2026-07-06T00:00:00Z"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period"]["from"] == "2026-07-05T00:00:00Z"
    assert body["period"]["to"] == "2026-07-06T00:00:00Z"
    assert body["metrics"]["consumption_by_location_per_day"] == [
        {"date": "2026-07-05", "location_id": "medellin_centro", "count": 1}
    ]


def test_report_invalid_date_422(client) -> None:
    response = client.get("/telemetry/report", params={"start_date": "not-a-date", "end_date": "2026-07-06T00:00:00Z"})
    assert response.status_code == 422


def test_report_only_one_param_422(client) -> None:
    response = client.get("/telemetry/report", params={"start_date": "2026-07-01T00:00:00Z"})
    assert response.status_code == 422


def test_default_period_cache_hit(client) -> None:
    with patch("report_service.run_report_pipeline", return_value=_sample_metrics()) as pipeline:
        first = client.get("/telemetry/report")
        second = client.get("/telemetry/report")

    assert pipeline.call_count == 1
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_explicit_period_cache_hit() -> None:
    fixed_now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    monotonic = {"value": 0.0}

    def monotonic_fn() -> float:
        return monotonic["value"]

    with patch("report_service.run_report_pipeline", return_value=_sample_metrics()) as pipeline:
        first = get_report_payload(
            "2026-07-01T00:00:00Z",
            "2026-07-08T00:00:00Z",
            lambda: fixed_now,
            monotonic_fn,
        )
        monotonic["value"] = 10.0
        second = get_report_payload(
            "2026-07-01T00:00:00Z",
            "2026-07-08T00:00:00Z",
            lambda: fixed_now,
            monotonic_fn,
        )

    assert pipeline.call_count == 1
    assert first == second


def test_cache_expired_reruns_pipeline() -> None:
    fixed_now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    monotonic = {"value": 0.0}

    def monotonic_fn() -> float:
        return monotonic["value"]

    with patch("report_service.run_report_pipeline", return_value=_sample_metrics()) as pipeline:
        get_report_payload(None, None, lambda: fixed_now, monotonic_fn)
        monotonic["value"] = 61.0
        get_report_payload(None, None, lambda: fixed_now, monotonic_fn)

    assert pipeline.call_count == 2


def test_different_explicit_params_separate_cache_entries() -> None:
    fixed_now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    monotonic = {"value": 0.0}

    def monotonic_fn() -> float:
        return monotonic["value"]

    with patch("report_service.run_report_pipeline", return_value=_sample_metrics()) as pipeline:
        get_report_payload(
            "2026-07-01T00:00:00Z",
            "2026-07-08T00:00:00Z",
            lambda: fixed_now,
            monotonic_fn,
        )
        get_report_payload(
            "2026-07-02T00:00:00Z",
            "2026-07-09T00:00:00Z",
            lambda: fixed_now,
            monotonic_fn,
        )

    assert pipeline.call_count == 2
