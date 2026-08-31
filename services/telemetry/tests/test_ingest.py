from __future__ import annotations

from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from db_models import TelemetryEventRow
from tests.conftest import sample_event


def test_valid_batch_is_stored_with_tags_and_level(client) -> None:
    response = client.post(
        "/telemetry/events",
        json={"events": [sample_event(), sample_event()]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"received": 2, "stored": 2, "rejected": 0}

    import database

    with database.get_session() as session:
        rows = session.exec(select(TelemetryEventRow)).all()

    assert len(rows) == 2
    assert rows[0].level == "info"
    assert rows[0].tags == {"location_id": "medellin_centro", "item_count": 3}
    assert rows[0].context["sessionId"] == "session-abc"


def test_mixed_batch_splits_stored_and_rejected(client) -> None:
    valid = sample_event()
    invalid = sample_event(event_type="not_a_real_event")

    response = client.post("/telemetry/events", json={"events": [valid, invalid]})

    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 1, "rejected": 1}


def test_extra_property_is_rejected_in_ingest(client) -> None:
    event = sample_event(
        properties={"location_id": "medellin_centro", "item_count": 3, "unexpected": True},
    )

    response = client.post("/telemetry/events", json={"events": [event]})

    assert response.status_code == 200
    assert response.json() == {"received": 1, "stored": 0, "rejected": 1}


def test_resending_identical_batch_counts_as_rejected(client) -> None:
    event = sample_event()
    first = client.post("/telemetry/events", json={"events": [event]})
    second = client.post("/telemetry/events", json={"events": [event]})

    assert first.json() == {"received": 1, "stored": 1, "rejected": 0}
    assert second.status_code == 200
    assert second.json() == {"received": 1, "stored": 0, "rejected": 1}


def test_received_equals_stored_plus_rejected(client) -> None:
    events = [
        sample_event(),
        sample_event(event_type="unknown_event"),
        sample_event(properties={"item_count": 1}),
    ]
    response = client.post("/telemetry/events", json={"events": events})
    body = response.json()

    assert body["received"] == body["stored"] + body["rejected"]


def test_bulk_insert_uses_single_execute(client) -> None:
    events = [sample_event(), sample_event(), sample_event()]

    with patch("repository.get_session") as get_session_mock:
        import database

        session = database.get_session()
        get_session_mock.return_value.__enter__.return_value = session

        with patch.object(session, "execute", wraps=session.execute) as execute_mock:
            response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    assert execute_mock.call_count == 1


def test_empty_events_returns_zero_counts(client) -> None:
    response = client.post("/telemetry/events", json={"events": []})

    assert response.status_code == 200
    assert response.json() == {"received": 0, "stored": 0, "rejected": 0}


def test_wrong_body_shape_returns_422(client) -> None:
    response = client.post("/telemetry/events", json={})

    assert response.status_code == 422


def test_events_not_a_list_returns_422(client) -> None:
    response = client.post("/telemetry/events", json={"events": "not-a-list"})

    assert response.status_code == 422


def test_db_failure_returns_503_not_500(client) -> None:
    with patch(
        "routers.telemetry.bulk_insert_events",
        side_effect=SQLAlchemyError("relation telemetry_events does not exist"),
    ):
        response = client.post(
            "/telemetry/events",
            json={"events": [sample_event()]},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "telemetry storage unavailable"}
