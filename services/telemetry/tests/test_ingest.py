from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from tests.conftest import sample_event


def test_valid_batch_returns_received_count(client: TestClient) -> None:
    response = client.post(
        "/telemetry/events",
        json={"events": [sample_event(), sample_event(event_type="user_login_succeeded")]},
    )

    assert response.status_code == 200
    assert response.json() == {"received": 2}


def test_empty_events_returns_zero(client: TestClient) -> None:
    response = client.post("/telemetry/events", json={"events": []})

    assert response.status_code == 200
    assert response.json() == {"received": 0}


def test_malformed_event_missing_envelope_field_logs_warning(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    malformed = sample_event()
    del malformed["service"]

    with caplog.at_level(logging.WARNING):
        response = client.post("/telemetry/events", json={"events": [malformed]})

    assert response.status_code == 200
    assert response.json() == {"received": 1}
    assert any("Rejected telemetry event at index 0" in record.message for record in caplog.records)


def test_mixed_valid_and_invalid_events_returns_total_count(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    malformed = sample_event()
    del malformed["eventId"]

    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/telemetry/events",
            json={"events": [sample_event(), malformed, sample_event()]},
        )

    assert response.status_code == 200
    assert response.json() == {"received": 3}
    assert any("Rejected telemetry event at index 1" in record.message for record in caplog.records)


def test_wrong_body_shape_returns_422(client: TestClient) -> None:
    response = client.post("/telemetry/events", json={})

    assert response.status_code == 422


def test_events_not_a_list_returns_422(client: TestClient) -> None:
    response = client.post("/telemetry/events", json={"events": "not-a-list"})

    assert response.status_code == 422
