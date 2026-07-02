from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from jose import jwt

from conftest import PRIVATE_PEM, make_access_token

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
