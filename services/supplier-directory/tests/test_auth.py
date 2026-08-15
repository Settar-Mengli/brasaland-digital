from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module


def test_supplier_routes_require_token() -> None:
    with TestClient(app_module.app) as client:
        assert client.get("/suppliers").status_code == 401
        assert (
            client.post(
                "/suppliers",
                json={
                    "name": "Anon",
                    "country": "Colombia",
                    "categories": ["meat"],
                    "rate_per_unit": 1.0,
                    "currency": "COP",
                    "status": "active",
                },
            ).status_code
            == 401
        )
        assert (
            client.patch(
                "/suppliers/1/rate", json={"rate_per_unit": 2.0}
            ).status_code
            == 401
        )
        assert client.delete("/suppliers/1").status_code == 401
