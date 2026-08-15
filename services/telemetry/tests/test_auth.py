from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import select

from db_models import TelemetryEventRow
from tests.conftest import sample_event


def test_report_requires_token() -> None:
    from app import app

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/telemetry/report").status_code == 401


def test_ingest_without_token_stores_anonymous_user() -> None:
    from app import app
    import database

    with TestClient(app, raise_server_exceptions=False) as anon:
        response = anon.post(
            "/telemetry/events",
            json={"events": [sample_event(userId="attacker")]},
        )

    assert response.status_code == 200
    with database.get_session() as session:
        rows = session.exec(select(TelemetryEventRow)).all()
    assert rows[0].context["userId"] == "anonymous"


def test_ingest_with_token_uses_jwt_identity(client) -> None:
    import database

    response = client.post(
        "/telemetry/events",
        json={"events": [sample_event(userId="attacker")]},
    )

    assert response.status_code == 200
    with database.get_session() as session:
        rows = session.exec(select(TelemetryEventRow)).all()
    assert rows[0].context["userId"] == "7"


def test_ingest_rejects_oversized_batch(client) -> None:
    events = [sample_event() for _ in range(51)]
    response = client.post("/telemetry/events", json={"events": events})
    assert response.status_code == 400
