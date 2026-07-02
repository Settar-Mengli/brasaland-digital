from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from conftest import make_access_token
from models import Ingredient, IngredientEntry, IngredientExit

BEEF_PAYLOAD = {
    "name": "Beef brisket",
    "sku": "BRS-BEEF-001",
    "unit": "kg",
    "category": "meat",
    "country": "CO",
}

INBOUND_PAYLOAD = {
    "ingredient_id": 0,
    "quantity": 25.0,
    "supplier_name": "Carnes del Valle S.A.",
    "location_id": 1,
}

OUTBOUND_PAYLOAD = {
    "ingredient_id": 0,
    "quantity": 10.0,
    "reason": "consumption",
    "location_id": 1,
}


def _auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_access_token(user_id)}"}


def _seed_beef(session: Session) -> Ingredient:
    beef = Ingredient.model_validate(BEEF_PAYLOAD)
    session.add(beef)
    session.commit()
    session.refresh(beef)
    return beef


def test_inbound_creates_entry_with_user_uuid_from_token(
    session: Session, client: TestClient
) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    payload = {**INBOUND_PAYLOAD, "ingredient_id": beef.id}

    response = client.post(
        "/inventory/orders/inbound",
        json=payload,
        headers=_auth_header(42),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_uuid"] == "42"
    assert body["supplier_name"] == "Carnes del Valle S.A."
    assert body["quantity"] == 25.0


def test_inbound_returns_404_for_missing_ingredient(client: TestClient) -> None:
    response = client.post(
        "/inventory/orders/inbound",
        json={**INBOUND_PAYLOAD, "ingredient_id": 9999},
        headers=_auth_header(1),
    )
    assert response.status_code == 404


def test_inbound_requires_auth(session: Session, client: TestClient) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    response = client.post(
        "/inventory/orders/inbound",
        json={**INBOUND_PAYLOAD, "ingredient_id": beef.id},
    )
    assert response.status_code == 401


def test_outbound_reduces_stock_and_persists_user_uuid(
    session: Session, client: TestClient
) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    session.add(
        IngredientEntry(
            ingredient_id=beef.id,
            quantity=50.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            user_uuid="1",
        )
    )
    session.commit()

    response = client.post(
        "/inventory/orders/outbound",
        json={**OUTBOUND_PAYLOAD, "ingredient_id": beef.id},
        headers=_auth_header(9),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_uuid"] == "9"
    assert body["reason"] == "consumption"

    products = client.get("/inventory/products").json()
    beef_product = next(item for item in products if item["sku"] == "BRS-BEEF-001")
    assert beef_product["current_stock"] == 40.0


def test_outbound_requires_auth(session: Session, client: TestClient) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    response = client.post(
        "/inventory/orders/outbound",
        json={**OUTBOUND_PAYLOAD, "ingredient_id": beef.id},
    )
    assert response.status_code == 401


def test_outbound_rejects_invalid_reason(session: Session, client: TestClient) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    response = client.post(
        "/inventory/orders/outbound",
        json={
            **OUTBOUND_PAYLOAD,
            "ingredient_id": beef.id,
            "reason": "spoilage",
        },
        headers=_auth_header(1),
    )
    assert response.status_code == 422
    assert response.json()["detail"] == 'reason must be "consumption" or "waste"'


def test_get_orders_returns_entries_and_exits_with_ingredient_data(
    session: Session, client: TestClient
) -> None:
    beef = _seed_beef(session)
    assert beef.id is not None
    session.add(
        IngredientEntry(
            ingredient_id=beef.id,
            quantity=30.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=2,
            user_uuid="3",
        )
    )
    session.add(
        IngredientExit(
            ingredient_id=beef.id,
            quantity=5.0,
            reason="waste",
            location_id=2,
            user_uuid="3",
        )
    )
    session.commit()

    response = client.get("/inventory/orders")
    assert response.status_code == 200
    body = response.json()
    assert len(body["entries"]) == 1
    assert len(body["exits"]) == 1

    entry = body["entries"][0]
    assert entry["supplier_name"] == "Carnes del Valle S.A."
    assert entry["ingredient"]["sku"] == "BRS-BEEF-001"
    assert entry["ingredient"]["country"] == "CO"

    exit_item = body["exits"][0]
    assert exit_item["reason"] == "waste"
    assert exit_item["ingredient"]["name"] == "Beef brisket"
