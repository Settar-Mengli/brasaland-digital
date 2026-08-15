from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module


def test_analyze_and_export_require_token() -> None:
    with TestClient(app_module.app) as client:
        assert client.post("/api/incidents/analyze").status_code == 401
        assert client.get("/api/incidents/results/export").status_code == 401
