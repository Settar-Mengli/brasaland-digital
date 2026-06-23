from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client() -> TestClient:
    with TestClient(app_module.app, raise_server_exceptions=False) as test_client:
        yield test_client


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Grill temperature issue",
        "description": "Customer reported undercooked steak at table 12",
        "category": "QUEJA_CLIENTE",
        "origin": "customer",
        "branch": "COL-01",
    }
    payload.update(overrides)
    return payload


def test_post_valid_incident_returns_201_with_open_status(client: TestClient) -> None:
    response = client.post("/api/incidents", json=_valid_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "open"
    assert data["title"] == "Grill temperature issue"
    assert data["created_at"]
    assert data["updated_at"]


def test_post_missing_required_fields_returns_accumulated_errors(client: TestClient) -> None:
    response = client.post(
        "/api/incidents",
        json={
            "title": "",
            "description": "",
            "category": "QUEJA_CLIENTE",
            "origin": "customer",
            "branch": "COL-01",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert "errors" in body["detail"]
    error_fields = {error["field"] for error in body["detail"]["errors"]}
    assert error_fields == {"title", "description"}
    assert len(body["detail"]["errors"]) == 2


def test_get_incidents_empty_returns_200_empty_list(client: TestClient) -> None:
    response = client.get("/api/incidents")

    assert response.status_code == 200
    assert response.json() == []


def test_get_incidents_filters_results(client: TestClient) -> None:
    client.post(
        "/api/incidents",
        json=_valid_payload(title="Open customer", status="open", origin="customer"),
    )
    client.post(
        "/api/incidents",
        json=_valid_payload(
            title="Branch issue",
            origin="branch",
            branch="COL-02",
            category="EQUIPAMIENTO",
        ),
    )
    client.post(
        "/api/incidents",
        json=_valid_payload(
            title="Internal note",
            origin="internal",
            branch="Central",
            category="PERSONAL",
        ),
    )

    all_response = client.get("/api/incidents")
    status_response = client.get("/api/incidents", params={"status": "open"})
    origin_response = client.get("/api/incidents", params={"origin": "branch"})
    branch_response = client.get("/api/incidents", params={"branch": "Central"})
    category_response = client.get("/api/incidents", params={"category": "EQUIPAMIENTO"})
    combined_response = client.get(
        "/api/incidents",
        params={"origin": "branch", "category": "EQUIPAMIENTO"},
    )

    assert len(all_response.json()) == 3
    assert len(status_response.json()) == 3
    assert len(origin_response.json()) == 1
    assert origin_response.json()[0]["title"] == "Branch issue"
    assert len(branch_response.json()) == 1
    assert branch_response.json()[0]["title"] == "Internal note"
    assert len(category_response.json()) == 1
    assert len(combined_response.json()) == 1


def test_get_incident_by_id_found_and_missing(client: TestClient) -> None:
    created = client.post("/api/incidents", json=_valid_payload()).json()

    found = client.get(f"/api/incidents/{created['id']}")
    missing = client.get("/api/incidents/999")

    assert found.status_code == 200
    assert found.json() == created
    assert missing.status_code == 404


def test_patch_legal_status_transition_updates_record(client: TestClient) -> None:
    created = client.post("/api/incidents", json=_valid_payload()).json()

    response = client.patch(
        f"/api/incidents/{created['id']}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["updated_at"] != created["updated_at"]


def test_patch_illegal_status_transition_returns_400(client: TestClient) -> None:
    created = client.post("/api/incidents", json=_valid_payload()).json()

    open_to_resolved = client.patch(
        f"/api/incidents/{created['id']}/status",
        json={"status": "resolved"},
    )

    assert open_to_resolved.status_code == 400
    assert open_to_resolved.json()["detail"] == "open cannot move directly to resolved"

    client.patch(
        f"/api/incidents/{created['id']}/status",
        json={"status": "in_progress"},
    )
    client.patch(
        f"/api/incidents/{created['id']}/status",
        json={"status": "resolved"},
    )

    from_terminal = client.patch(
        f"/api/incidents/{created['id']}/status",
        json={"status": "discarded"},
    )

    assert from_terminal.status_code == 400
    assert "terminal state 'resolved'" in from_terminal.json()["detail"]


def test_patch_missing_incident_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/incidents/999/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 404


def test_get_summary_on_empty_db_returns_zero_totals(client: TestClient) -> None:
    response = client.get("/api/incidents/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "by_status": {},
        "by_category": {},
        "by_origin": {},
        "by_branch": {},
    }


def test_summary_route_is_not_captured_by_id_route(client: TestClient) -> None:
    response = client.get("/api/incidents/summary")

    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "by_status" in body
    assert "by_category" in body
    assert "by_origin" in body
    assert "by_branch" in body


def test_unhandled_exception_returns_generic_500_without_traceback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_runtime_error(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("secret internal path /var/secret")

    monkeypatch.setattr(app_module, "create_incident", _raise_runtime_error)

    response = client.post("/api/incidents", json=_valid_payload())

    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": "An unexpected error occurred."}
    assert "traceback" not in body
    assert "stack" not in body
    assert "secret" not in str(body)
