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


def test_incident_reads_remain_public() -> None:
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        assert client.get("/api/incidents").status_code == 200
        assert client.get("/api/incidents/summary").status_code == 200
