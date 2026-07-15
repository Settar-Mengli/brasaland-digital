from __future__ import annotations

from pathlib import Path

from allowlists import load_allowlists, validate_event_properties


def test_all_catalog_event_types_have_required_keys() -> None:
    allowlists = load_allowlists()
    assert len(allowlists) == 11
    assert allowlists["ingredient_list_viewed"] == frozenset({"location_id", "item_count"})


def test_missing_required_property_is_rejected() -> None:
    error = validate_event_properties("ingredient_list_viewed", {"item_count": 3})
    assert error == "missing required property: location_id"


def test_unknown_event_type_is_rejected() -> None:
    error = validate_event_properties("not_a_real_event", {"location_id": "medellin_centro"})
    assert error == "unknown event_type: not_a_real_event"


def test_extra_property_is_rejected() -> None:
    error = validate_event_properties(
        "ingredient_list_viewed",
        {"location_id": "medellin_centro", "item_count": 3, "unexpected": True},
    )
    assert error == "unexpected properties: unexpected"


def test_bundled_schema_matches_repo_docs_when_present() -> None:
    docs_path = Path(__file__).resolve().parents[3] / "docs" / "telemetry" / "event-schemas.json"
    bundled_path = Path(__file__).resolve().parents[1] / "allowlists" / "event-schemas.json"
    if not docs_path.exists():
        return
    assert docs_path.read_text(encoding="utf-8") == bundled_path.read_text(encoding="utf-8")


def test_supply_unit_cost_optional_and_not_on_consumption() -> None:
    supply_base = {
        "supply_order_id": 1,
        "ingredient_id": 1,
        "quantity": 10.0,
        "supplier_id": 0,
        "location_id": "medellin_centro",
        "created_by": "42",
    }
    assert validate_event_properties("supply_order_created", {**supply_base, "unit_cost": 12.5}) is None
    assert validate_event_properties("supply_order_created", supply_base) is None

    consumption_with_cost = {
        "consumption_order_id": 1,
        "ingredient_id": 1,
        "quantity": 5.0,
        "reason": "waste",
        "location_id": "medellin_centro",
        "created_by": "42",
        "restricted_access": False,
        "unit_cost": 12.5,
    }
    error = validate_event_properties("consumption_order_created", consumption_with_cost)
    assert error == "unexpected properties: unit_cost"
