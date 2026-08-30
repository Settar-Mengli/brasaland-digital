"""Drift guards for docs/public-knowledge-base guest corpus."""

from __future__ import annotations

import json
from pathlib import Path

from pipelines.locations import LOCATION_DIMENSIONS

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ROOT = REPO_ROOT / "docs" / "public-knowledge-base"
MANUAL_ALLERGEN_PATH = REPO_ROOT / "docs" / "company-knowledge-base" / "menu-allergens.md"

INTERNAL_FIELD_BANS = (
    "manager",
    "rent",
    "staff",
    "ingredient",
    "prep_time",
    "seating",
    "monthly",
)

ALLERGEN_ANCHORS: list[tuple[str, list[str]]] = [
    ("Grilled Sirloin (Lomo a la Brasa)", ["soy"]),
    ("Brasaland BBQ Ribs", ["soy"]),
    ("Classic Grilled Chicken", []),
    ("Tropical Salad", ["nuts", "dairy"]),
    ("Corn Arepa", ["dairy", "egg"]),
    ("House Sauce", ["soy", "sulfites"]),
]

ALLOWLIST_EXEMPT = frozenset({"README.md", "manifest.json"})


def _load_json(name: str) -> dict:
    return json.loads((PUBLIC_ROOT / name).read_text(encoding="utf-8"))


def _collect_keys(obj: object, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            full = f"{prefix}.{key}" if prefix else key
            keys.add(full.lower())
            keys.update(_collect_keys(value, full))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(_collect_keys(item, prefix))
    return keys


def test_public_location_slugs_match_canon() -> None:
    locations = _load_json("locations.json")["locations"]
    slugs = {loc["slug"] for loc in locations}
    assert slugs == set(LOCATION_DIMENSIONS.keys())
    assert len(slugs) == 14


def test_public_location_country_currency() -> None:
    locations = _load_json("locations.json")["locations"]
    for loc in locations:
        country_code, currency = LOCATION_DIMENSIONS[loc["slug"]]
        assert loc["country_code"] == country_code
        assert loc["currency"] == currency
        if country_code == "CO":
            assert currency == "COP"
        else:
            assert currency == "USD"


def test_menu_ids_unique_and_prices_valid() -> None:
    items = _load_json("menu.json")["items"]
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))
    for item in items:
        assert item["is_complete"] is True
        markets = item["markets"]
        price = item["price"]
        if markets.get("CO"):
            assert isinstance(price["COP"], int)
        else:
            assert price["COP"] is None
        if markets.get("US"):
            assert isinstance(price["USD"], int)
        else:
            assert price["USD"] is None


def test_manifest_allowlist_only_public_files() -> None:
    manifest = _load_json("manifest.json")
    listed_paths = {entry["path"] for entry in manifest["sources"]}
    on_disk = {
        p.name
        for p in PUBLIC_ROOT.iterdir()
        if p.is_file() and p.name not in ALLOWLIST_EXEMPT
    }
    assert listed_paths == on_disk
    for entry in manifest["sources"]:
        path = entry["path"]
        assert "company-knowledge-base" not in path
        assert not path.startswith("/")
        assert Path(path).parent == Path(".")


def test_no_internal_fields_in_public_json() -> None:
    for name in ("locations.json", "menu.json"):
        keys = _collect_keys(_load_json(name))
        for banned in INTERNAL_FIELD_BANS:
            assert not any(banned in key for key in keys)


def test_public_loyalty_matches_manual_earn_facts() -> None:
    loyalty = (PUBLIC_ROOT / "loyalty.md").read_text(encoding="utf-8")
    assert "10,000 COP" in loyalty
    assert "10 USD" in loyalty


def test_allergen_anchor_dishes_in_menu() -> None:
    items = _load_json("menu.json")["items"]
    by_name = {item["name"]: item for item in items}
    for name, expected_allergens in ALLERGEN_ANCHORS:
        assert name in by_name
        item_allergens = set(by_name[name]["allergens"])
        for allergen in expected_allergens:
            assert allergen in item_allergens


def test_manual_allergen_doc_lists_anchor_dishes() -> None:
    manual = MANUAL_ALLERGEN_PATH.read_text(encoding="utf-8")
    for name, _ in ALLERGEN_ANCHORS:
        assert name in manual
