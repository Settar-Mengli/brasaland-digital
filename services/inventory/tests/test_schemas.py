from __future__ import annotations

from datetime import UTC, datetime

from schemas import (
    IngredientCreate,
    IngredientEntryCreate,
    IngredientEntryResponse,
    IngredientExitCreate,
    IngredientExitResponse,
    IngredientResponse,
)


def test_ingredient_response_includes_current_stock() -> None:
    payload = {
        "id": 1,
        "name": "Beef brisket",
        "sku": "BRS-BEEF-001",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
        "current_stock": 80.0,
    }
    parsed = IngredientResponse.model_validate(payload)
    assert parsed.current_stock == 80.0
    assert parsed.country == "CO"


def test_ingredient_create_has_no_current_stock() -> None:
    payload = {
        "name": "Beef brisket",
        "sku": "BRS-BEEF-001",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
    }
    parsed = IngredientCreate.model_validate(payload)
    assert "current_stock" not in IngredientCreate.model_fields


def test_entry_request_excludes_user_uuid() -> None:
    payload = {
        "ingredient_id": 1,
        "quantity": 50.0,
        "supplier_name": "Carnes del Valle S.A.",
        "location_id": 3,
    }
    parsed = IngredientEntryCreate.model_validate(payload)
    assert parsed.supplier_name == "Carnes del Valle S.A."
    assert "user_uuid" not in IngredientEntryCreate.model_fields


def test_entry_response_includes_user_uuid() -> None:
    created_at = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    payload = {
        "id": 1,
        "ingredient_id": 1,
        "quantity": 50.0,
        "supplier_name": "Carnes del Valle S.A.",
        "location_id": 3,
        "created_at": created_at,
        "user_uuid": "supervisor-uuid-1",
    }
    parsed = IngredientEntryResponse.model_validate(payload)
    assert parsed.user_uuid == "supervisor-uuid-1"


def test_exit_request_excludes_user_uuid() -> None:
    payload = {
        "ingredient_id": 1,
        "quantity": 5.0,
        "reason": "waste",
        "location_id": 2,
    }
    parsed = IngredientExitCreate.model_validate(payload)
    assert parsed.reason == "waste"
    assert "user_uuid" not in IngredientExitCreate.model_fields


def test_exit_response_includes_user_uuid() -> None:
    created_at = datetime(2026, 1, 16, 8, 30, tzinfo=UTC)
    payload = {
        "id": 1,
        "ingredient_id": 1,
        "quantity": 5.0,
        "reason": "consumption",
        "location_id": 2,
        "created_at": created_at,
        "user_uuid": "staff-uuid-2",
    }
    parsed = IngredientExitResponse.model_validate(payload)
    assert parsed.reason == "consumption"
    assert parsed.user_uuid == "staff-uuid-2"
