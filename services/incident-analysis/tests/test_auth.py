from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


def _analyze(client: TestClient) -> str:
    with FIXTURE_PATH.open("rb") as handle:
        response = client.post(
            "/api/incidents/analyze",
            files={"file": ("incidents-brasaland.csv", handle, "text/csv")},
        )
    assert response.status_code == 200
    return response.json()["result_id"]


def test_analyze_and_export_require_token() -> None:
    with TestClient(app_module.app) as client:
        assert client.post("/api/incidents/analyze").status_code == 401
        assert (
            client.get(
                "/api/incidents/results/00000000-0000-0000-0000-000000000000/export"
            ).status_code
            == 401
        )


def test_owner_can_export_own_result(mint_headers) -> None:
    headers = mint_headers(user_id=11)
    with TestClient(app_module.app, headers=headers) as client:
        result_id = _analyze(client)
        response = client.get(f"/api/incidents/results/{result_id}/export")
    assert response.status_code == 200
    assert response.text.startswith("metric,value,percentage")


def test_non_owner_cannot_export(mint_headers) -> None:
    owner = mint_headers(user_id=21)
    other = mint_headers(user_id=22)
    with TestClient(app_module.app, headers=owner) as owner_client:
        result_id = _analyze(owner_client)

    with TestClient(app_module.app, headers=other) as other_client:
        response = other_client.get(f"/api/incidents/results/{result_id}/export")

    assert response.status_code == 403
    assert response.json()["detail"] == app_module.NOT_ALLOWED_TO_EXPORT


def test_admin_can_export_any_result(mint_headers) -> None:
    owner = mint_headers(user_id=31)
    admin = mint_headers(user_id=99, is_admin=True)
    with TestClient(app_module.app, headers=owner) as owner_client:
        result_id = _analyze(owner_client)

    with TestClient(app_module.app, headers=admin) as admin_client:
        response = admin_client.get(f"/api/incidents/results/{result_id}/export")

    assert response.status_code == 200


def test_expired_result_returns_404(mint_headers) -> None:
    from datetime import datetime, timedelta, timezone

    headers = mint_headers(user_id=41)
    with TestClient(app_module.app, headers=headers) as client:
        result_id = _analyze(client)

        from result_store import result_store

        stored = result_store.get(result_id)
        assert stored is not None
        # Force expiry without waiting for the real TTL.
        expired = stored.__class__(
            result_id=stored.result_id,
            owner_user_uuid=stored.owner_user_uuid,
            result=stored.result,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        with result_store._lock:
            result_store._entries[result_id] = expired

        response = client.get(f"/api/incidents/results/{result_id}/export")

    assert response.status_code == 404
    assert response.json()["detail"] == app_module.RESULT_NOT_FOUND
