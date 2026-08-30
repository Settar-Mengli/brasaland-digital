from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session

from conftest import PRIVATE_PEM, make_access_token
from models import Ingredient

PRODUCT_PAYLOAD = {
    "name": "Yuca (cassava)",
    "sku": "BRS-PROD-001",
    "unit": "kg",
    "category": "produce",
    "country": "CO",
}


def test_post_product_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/inventory/products", json=PRODUCT_PAYLOAD)
    assert response.status_code == 401


def test_post_product_with_refresh_token_returns_401(client: TestClient) -> None:
    expire_at = datetime.now(UTC) + timedelta(minutes=30)
    refresh_token = jwt.encode(
        {
            "sub": "42",
            "user_id": 42,
            "type": "refresh",
            "exp": int(expire_at.timestamp()),
        },
        PRIVATE_PEM,
        algorithm="RS256",
    )
    response = client.post(
        "/inventory/products",
        json=PRODUCT_PAYLOAD,
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_post_product_with_valid_access_token_succeeds(client: TestClient) -> None:
    token = make_access_token(42)
    response = client.post(
        "/inventory/products",
        json=PRODUCT_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["sku"] == PRODUCT_PAYLOAD["sku"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_inventory_reads_without_token_return_401(client: TestClient) -> None:
    assert client.get("/inventory/products", params={"location_id": 1}).status_code == 401
    assert client.get("/inventory/products/1", params={"location_id": 1}).status_code == 401
    assert client.get("/inventory/orders", params={"location_id": 1}).status_code == 401


def test_scoped_user_can_read_an_authorized_location(
    client: TestClient,
) -> None:
    token = make_access_token(
        42,
        authorized_locations=["medellin_centro"],
        location_slug="medellin_centro",
    )
    headers = _headers(token)

    products = client.get("/inventory/products", params={"location_id": 1}, headers=headers)
    orders = client.get("/inventory/orders", params={"location_id": 1}, headers=headers)

    assert products.status_code == 200
    assert orders.status_code == 200


def test_scoped_user_gets_403_for_unauthorized_location(
    client: TestClient,
) -> None:
    token = make_access_token(
        42,
        authorized_locations=["medellin_centro"],
        location_slug="medellin_centro",
    )
    headers = _headers(token)

    for path in (
        "/inventory/products",
        "/inventory/products/1",
        "/inventory/orders",
    ):
        response = client.get(path, params={"location_id": 2}, headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Location access denied"


def test_admin_can_read_any_location(
    session: Session,
    client: TestClient,
) -> None:
    ingredient = Ingredient.model_validate(PRODUCT_PAYLOAD)
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    assert ingredient.id is not None
    headers = _headers(make_access_token(1, is_admin=True))

    products = client.get("/inventory/products", params={"location_id": 14}, headers=headers)
    detail = client.get(
        f"/inventory/products/{ingredient.id}",
        params={"location_id": 14},
        headers=headers,
    )
    orders = client.get("/inventory/orders", params={"location_id": 14}, headers=headers)

    assert products.status_code == 200
    assert detail.status_code == 200
    assert orders.status_code == 200
