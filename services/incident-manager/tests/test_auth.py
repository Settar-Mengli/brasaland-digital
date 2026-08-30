from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module


def test_incident_mutations_require_token() -> None:
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        assert (
            client.post(
                "/api/incidents",
                json={
                    "title": "Anon",
                    "description": "Should be rejected",
                    "category": "QUEJA_CLIENTE",
                    "origin": "customer",
                    "branch": "COL-01",
                },
            ).status_code
            == 401
        )
        assert (
            client.patch(
                "/api/incidents/1/status",
                json={"status": "in_progress"},
            ).status_code
            == 401
        )


def test_incident_reads_require_token() -> None:
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        assert client.get("/api/incidents").status_code == 401
        assert client.get("/api/incidents/summary").status_code == 401
        assert client.get("/api/incidents/1").status_code == 401


def test_incident_reads_accept_valid_access_token(
    auth_headers: dict[str, str],
) -> None:
    with TestClient(
        app_module.app,
        raise_server_exceptions=False,
        headers=auth_headers,
    ) as client:
        created = client.post(
            "/api/incidents",
            json={
                "title": "Authenticated",
                "description": "Visible to authenticated staff",
                "category": "QUEJA_CLIENTE",
                "origin": "customer",
                "branch": "COL-01",
            },
        )
        assert created.status_code == 201
        incident_id = created.json()["id"]
        assert client.get("/api/incidents").status_code == 200
        assert client.get("/api/incidents/summary").status_code == 200
        assert client.get(f"/api/incidents/{incident_id}").status_code == 200
