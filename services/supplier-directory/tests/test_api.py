from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client(auth_headers: dict[str, str]) -> TestClient:
    with TestClient(app_module.app, headers=auth_headers) as test_client:
        yield test_client


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Test Supplier",
        "country": "Colombia",
        "categories": ["meat"],
        "rate_per_unit": 1000.0,
        "currency": "COP",
        "status": "active",
    }
    payload.update(overrides)
    return payload


def test_post_valid_supplier_returns_201(client: TestClient) -> None:
    response = client.post("/suppliers", json=_valid_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Supplier"
    assert data["country"] == "Colombia"
    assert data["categories"] == ["meat"]
    assert data["rate_per_unit"] == 1000.0
    assert data["currency"] == "COP"
    assert data["status"] == "active"
    assert data["rate_updated_at"]


def test_post_currency_mismatch_returns_422_without_write(client: TestClient) -> None:
    response = client.post(
        "/suppliers",
        json=_valid_payload(country="Colombia", currency="USD"),
    )

    assert response.status_code == 422
    assert "currency must be COP for country Colombia" in response.json()["detail"]
    assert client.get("/suppliers").json() == []


def test_post_missing_status_returns_422(client: TestClient) -> None:
    payload = _valid_payload()
    del payload["status"]

    response = client.post("/suppliers", json=payload)

    assert response.status_code == 422


def test_post_bad_category_returns_422(client: TestClient) -> None:
    response = client.post(
        "/suppliers",
        json=_valid_payload(categories=["invalid_category"]),
    )

    assert response.status_code == 422
    assert "categories must contain only valid category values" in response.json()["detail"]


def test_post_empty_name_returns_422_without_write(client: TestClient) -> None:
    response = client.post(
        "/suppliers",
        json=_valid_payload(name="   "),
    )

    assert response.status_code == 422
    assert "name is required" in response.json()["detail"]
    assert client.get("/suppliers").json() == []


def test_get_suppliers_empty_returns_200(client: TestClient) -> None:
    response = client.get("/suppliers")

    assert response.status_code == 200
    assert response.json() == []


def test_get_suppliers_invalid_category_returns_422(client: TestClient) -> None:
    response = client.get("/suppliers", params={"category": "bogus"})

    assert response.status_code == 422
    assert response.json()["detail"] == ["category must be a valid category value"]


def test_get_suppliers_filters(client: TestClient) -> None:
    client.post(
        "/suppliers",
        json=_valid_payload(name="Colombia Meat", categories=["meat"]),
    )
    client.post(
        "/suppliers",
        json=_valid_payload(
            name="USA Meat",
            country="USA",
            currency="USD",
            categories=["meat"],
        ),
    )
    client.post(
        "/suppliers",
        json=_valid_payload(
            name="Colombia Veg",
            categories=["vegetables_and_greens"],
        ),
    )

    all_response = client.get("/suppliers")
    colombia_response = client.get("/suppliers", params={"country": "Colombia"})
    meat_response = client.get("/suppliers", params={"category": "meat"})
    combined_response = client.get(
        "/suppliers",
        params={"country": "Colombia", "category": "meat"},
    )

    assert len(all_response.json()) == 3
    assert len(colombia_response.json()) == 2
    assert {item["name"] for item in colombia_response.json()} == {
        "Colombia Meat",
        "Colombia Veg",
    }
    assert len(meat_response.json()) == 2
    assert {item["name"] for item in meat_response.json()} == {
        "Colombia Meat",
        "USA Meat",
    }
    assert len(combined_response.json()) == 1
    assert combined_response.json()[0]["name"] == "Colombia Meat"


def test_get_supplier_by_id(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()

    found = client.get(f"/suppliers/{created['id']}")
    missing = client.get("/suppliers/999")

    assert found.status_code == 200
    assert found.json() == created
    assert missing.status_code == 404


def test_patch_rate_updates_rate_and_timestamp(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()
    original_timestamp = created["rate_updated_at"]

    time.sleep(0.01)

    response = client.patch(
        f"/suppliers/{created['id']}/rate",
        json={"rate_per_unit": 1500.0},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["rate_per_unit"] == 1500.0
    assert updated["rate_updated_at"] != original_timestamp


def test_patch_rate_zero_returns_422(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()

    response = client.patch(
        f"/suppliers/{created['id']}/rate",
        json={"rate_per_unit": 0},
    )

    assert response.status_code == 422


def test_patch_rate_missing_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/suppliers/999/rate",
        json={"rate_per_unit": 1500.0},
    )

    assert response.status_code == 404


def test_patch_status_updates_status(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()

    response = client.patch(
        f"/suppliers/{created['id']}/status",
        json={"status": "suspended"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


def test_patch_status_invalid_returns_422(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()

    response = client.patch(
        f"/suppliers/{created['id']}/status",
        json={"status": "inactive"},
    )

    assert response.status_code == 422


def test_patch_status_missing_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/suppliers/999/status",
        json={"status": "suspended"},
    )

    assert response.status_code == 404


def test_delete_existing_then_get_returns_404(client: TestClient) -> None:
    created = client.post("/suppliers", json=_valid_payload()).json()

    delete_response = client.delete(f"/suppliers/{created['id']}")
    get_response = client.get(f"/suppliers/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    response = client.delete("/suppliers/999")

    assert response.status_code == 404
