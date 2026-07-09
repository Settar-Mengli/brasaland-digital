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
