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

SAUCE_PAYLOAD = {
    "name": "Chimichurri sauce",
    "sku": "BRS-SAUCE-001",
    "unit": "litre",
    "category": "sauce",
    "country": "CO",
}


def _auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_access_token(user_id)}"}


def _seed_stock_fixtures(session: Session) -> Ingredient:
    beef = Ingredient.model_validate(BEEF_PAYLOAD)
    sauce = Ingredient.model_validate(SAUCE_PAYLOAD)
    session.add(beef)
    session.add(sauce)
    session.commit()
    session.refresh(beef)
    session.refresh(sauce)

    session.add(
        IngredientEntry(
            ingredient_id=beef.id,
            quantity=50.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            user_uuid="7",
        )
    )
    session.add(
        IngredientEntry(
            ingredient_id=beef.id,
            quantity=30.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            user_uuid="7",
        )
    )
    session.add(
        IngredientExit(
            ingredient_id=beef.id,
            quantity=20.0,
            reason="consumption",
            location_id=1,
            user_uuid="7",
        )
    )
    session.commit()
    return beef


def test_get_products_returns_schemas_with_country_and_stock(
    session: Session,
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    _seed_stock_fixtures(session)

    response = client.get(
        "/inventory/products",
        params={"location_id": 1},
        headers=admin_headers,
    )
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)

    beef = next(item for item in products if item["sku"] == "BRS-BEEF-001")
    assert beef["country"] == "CO"
    assert beef["current_stock"] == 60.0
    assert set(beef) == {
        "id",
        "name",
        "sku",
        "unit",
        "category",
        "country",
        "current_stock",
    }

    sauce = next(item for item in products if item["sku"] == "BRS-SAUCE-001")
    assert sauce["current_stock"] == 0.0


def test_get_product_detail_returns_schema_with_stock(
    session: Session,
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    beef = _seed_stock_fixtures(session)
    assert beef.id is not None

    response = client.get(
        f"/inventory/products/{beef.id}",
        params={"location_id": 1},
        headers=admin_headers,
    )
    assert response.status_code == 200
    product = response.json()
    assert product["country"] == "CO"
    assert product["current_stock"] == 60.0


def test_get_product_detail_returns_404_when_missing(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.get(
        "/inventory/products/9999",
        params={"location_id": 1},
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_post_product_creates_ingredient_with_zero_stock(
    client: TestClient,
) -> None:
    response = client.post(
        "/inventory/products",
        json=BEEF_PAYLOAD,
        headers=_auth_header(3),
    )
    assert response.status_code == 200
    created = response.json()
    assert created["sku"] == "BRS-BEEF-001"
    assert created["country"] == "CO"
    assert created["current_stock"] == 0.0
