from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent / "allowlists" / "event-schemas.json"

CATALOG_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "supply_order_created",
        "supply_order_failed",
        "consumption_order_created",
        "consumption_order_failed",
        "stock_threshold_triggered",
        "direct_stock_edit_rejected",
        "user_login_failed",
        "session_expired",
        "order_form_abandoned",
        "ingredient_list_viewed",
        "user_login_succeeded",
    }
)


def resolve_schema_path() -> Path:
    override = os.getenv("TELEMETRY_SCHEMA_PATH")
    if override:
        return Path(override)
    return DEFAULT_SCHEMA_PATH


@lru_cache(maxsize=1)
def load_allowlists() -> dict[str, frozenset[str]]:
    path = resolve_schema_path()
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    definitions = schema.get("definitions", {})
    allowlists: dict[str, frozenset[str]] = {}

    for name, definition in definitions.items():
        if name not in CATALOG_EVENT_TYPES:
            continue
        properties_block = _extract_properties_block(definition)
        if properties_block is None:
            continue
        required = properties_block.get("required", [])
        allowlists[name] = frozenset(required)

    missing = CATALOG_EVENT_TYPES.difference(allowlists)
    if missing:
        missing_names = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing allowlist definitions for: {missing_names}")

    return allowlists


@lru_cache(maxsize=1)
def load_allowed_property_keys() -> dict[str, frozenset[str]]:
    path = resolve_schema_path()
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    definitions = schema.get("definitions", {})
    allowed: dict[str, frozenset[str]] = {}

    for name, definition in definitions.items():
        if name not in CATALOG_EVENT_TYPES:
            continue
        properties_block = _extract_properties_block(definition)
        if properties_block is None:
            continue
        property_names = properties_block.get("properties", {})
        allowed[name] = frozenset(property_names.keys())

    return allowed


def _extract_properties_block(definition: dict[str, Any]) -> dict[str, Any] | None:
    for item in definition.get("allOf", []):
        properties = item.get("properties", {})
        nested = properties.get("properties")
        if isinstance(nested, dict) and "type" in nested:
            return nested
    return None


def validate_event_properties(event_type: str, properties: dict[str, Any]) -> str | None:
    allowlists = load_allowlists()
    allowed_keys = load_allowed_property_keys()

    if event_type not in allowlists:
        return f"unknown event_type: {event_type}"

    required = allowlists[event_type]
    allowed = allowed_keys.get(event_type, frozenset())

    for key in required:
        if key not in properties:
            return f"missing required property: {key}"

    extra_keys = set(properties).difference(allowed)
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        return f"unexpected properties: {extras}"

    return None
