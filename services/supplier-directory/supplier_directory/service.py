from __future__ import annotations

from datetime import datetime, timezone

from supplier_directory.constants import VALID_STATUSES
from supplier_directory.repository import (
    delete,
    find_by_name_country,
    get,
    insert,
    list_all,
    update,
)
from supplier_directory.types import SupplierInput, SupplierRecord
from supplier_directory.validator import validate_rate, validate_supplier


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_categories(categories: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for category in categories:
        if category not in seen:
            seen.add(category)
            result.append(category)
    return result


def _normalize_supplier_input(data: SupplierInput) -> SupplierInput:
    normalized: SupplierInput = dict(data)
    categories = data.get("categories")
    if isinstance(categories, list):
        normalized["categories"] = _dedupe_categories(categories)
    return normalized


def create(data: SupplierInput) -> SupplierRecord:
    normalized = _normalize_supplier_input(data)
    validate_supplier(normalized)
    record = {
        **normalized,
        "rate_updated_at": _utc_now_iso(),
    }
    return insert(record)


def list_suppliers(
    country: str | None = None,
    category: str | None = None,
) -> list[SupplierRecord]:
    return list_all(country=country, category=category)


def get_supplier(supplier_id: int) -> SupplierRecord | None:
    return get(supplier_id)


def update_rate(supplier_id: int, new_rate: float) -> SupplierRecord | None:
    validate_rate(new_rate)
    if get(supplier_id) is None:
        return None
    return update(
        supplier_id,
        {
            "rate_per_unit": float(new_rate),
            "rate_updated_at": _utc_now_iso(),
        },
    )


def update_status(supplier_id: int, new_status: str) -> SupplierRecord | None:
    if new_status not in VALID_STATUSES:
        from supplier_directory.types import SupplierValidationError

        raise SupplierValidationError(("status must be active or suspended",))
    if get(supplier_id) is None:
        return None
    return update(supplier_id, {"status": new_status})


def delete_supplier(supplier_id: int) -> bool:
    return delete(supplier_id)


def seed_batch(records: list[SupplierInput]) -> tuple[int, int]:
    inserted_count = 0
    skipped_count = 0

    for record in records:
        if find_by_name_country(record["name"], record["country"]) is not None:
            skipped_count += 1
            continue

        normalized = _normalize_supplier_input(record)
        validate_supplier(normalized)
        insert(
            {
                **normalized,
                "rate_updated_at": _utc_now_iso(),
            }
        )
        inserted_count += 1

    return inserted_count, skipped_count
