from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlmodel import Session

from conftest import make_access_token
from models import Ingredient, IngredientEntry, IngredientExit
from routers.inventory import INSUFFICIENT_STOCK_MESSAGE

BEEF_PAYLOAD = {
    "name": "Beef brisket",
    "sku": "BRS-BEEF-001",
    "unit": "kg",
    "category": "meat",
    "country": "CO",
}


def _auth_header(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_access_token(user_id)}"}


def test_advisory_lock_compiles_to_postgres_sql() -> None:
    """Outbound lock statement must emit pg_advisory_xact_lock on PostgreSQL."""
    stmt = text("SELECT pg_advisory_xact_lock(:ingredient_id, :location_id)").bindparams(
        ingredient_id=1, location_id=2
    )
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "pg_advisory_xact_lock" in compiled.lower()


def _seed_beef_with_stock(session: Session) -> Ingredient:
    beef = Ingredient.model_validate(BEEF_PAYLOAD)
    session.add(beef)
    session.commit()
    session.refresh(beef)
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
    session.add(
        IngredientEntry(
            ingredient_id=beef.id,
            quantity=30.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            user_uuid="1",
        )
    )
    session.add(
        IngredientExit(
            ingredient_id=beef.id,
            quantity=20.0,
            reason="consumption",
            location_id=1,
            user_uuid="1",
        )
    )
    session.commit()
    return beef


def test_current_stock_reflects_entries_minus_exits_at_location(
    session: Session,
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    _seed_beef_with_stock(session)

    response = client.get(
        "/inventory/products",
        params={"location_id": 1},
        headers=admin_headers,
    )
    beef = next(item for item in response.json() if item["sku"] == "BRS-BEEF-001")
    assert beef["current_stock"] == 60.0


def test_cross_location_stock_is_isolated(
    session: Session,
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    beef = _seed_beef_with_stock(session)
    assert beef.id is not None

    location_two = client.get(
        "/inventory/products",
        params={"location_id": 2},
        headers=admin_headers,
    ).json()
    beef_at_two = next(item for item in location_two if item["sku"] == "BRS-BEEF-001")
    assert beef_at_two["current_stock"] == 0.0

    response = client.post(
        "/inventory/orders/outbound",
        json={
            "ingredient_id": beef.id,
            "quantity": 10.0,
            "reason": "consumption",
            "location_id": 2,
        },
        headers=_auth_header(1),
    )
    assert response.status_code == 400
    expected = INSUFFICIENT_STOCK_MESSAGE.format(
        name="Beef brisket",
        available=0.0,
        requested=10.0,
    )
    assert response.json()["detail"] == expected


def test_outbound_exceeding_stock_returns_exact_400_message(
    session: Session, client: TestClient
) -> None:
    beef = _seed_beef_with_stock(session)
    assert beef.id is not None

    response = client.post(
        "/inventory/orders/outbound",
        json={
            "ingredient_id": beef.id,
            "quantity": 61.0,
            "reason": "consumption",
            "location_id": 1,
        },
        headers=_auth_header(1),
    )
    assert response.status_code == 400
    expected = INSUFFICIENT_STOCK_MESSAGE.format(
        name="Beef brisket",
        available=60.0,
        requested=61.0,
    )
    assert response.json()["detail"] == expected


def test_outbound_exactly_equal_to_available_succeeds_and_zeroes_stock(
    session: Session,
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    beef = _seed_beef_with_stock(session)
    assert beef.id is not None

    response = client.post(
        "/inventory/orders/outbound",
        json={
            "ingredient_id": beef.id,
            "quantity": 60.0,
            "reason": "waste",
            "location_id": 1,
        },
        headers=_auth_header(1),
    )
    assert response.status_code == 200

    products = client.get(
        "/inventory/products",
        params={"location_id": 1},
        headers=admin_headers,
    ).json()
    beef_product = next(item for item in products if item["sku"] == "BRS-BEEF-001")
    assert beef_product["current_stock"] == 0.0


def test_products_requires_location_id_query_param(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.get("/inventory/products", headers=admin_headers)
    assert response.status_code == 422
