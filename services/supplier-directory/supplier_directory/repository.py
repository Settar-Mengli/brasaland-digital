from __future__ import annotations

from typing import Any

from tinydb import Query

from supplier_directory.db import get_db
from supplier_directory.types import SupplierRecord


def _table() -> Any:
    return get_db().table("suppliers")


def _next_id(records: list[SupplierRecord]) -> int:
    if not records:
        return 1
    return max(record["id"] for record in records) + 1


def insert(record: dict[str, Any]) -> SupplierRecord:
    table = _table()
    existing = table.all()
    supplier_id = _next_id(existing)
    stored: SupplierRecord = {
        "id": supplier_id,
        "name": record["name"],
        "country": record["country"],
        "categories": list(record["categories"]),
        "rate_per_unit": float(record["rate_per_unit"]),
        "currency": record["currency"],
        "rate_updated_at": record["rate_updated_at"],
        "status": record["status"],
        "contact_email": record.get("contact_email"),
        "notes": record.get("notes"),
    }
    table.insert(stored)
    return stored


def get(supplier_id: int) -> SupplierRecord | None:
    query = Query()
    result = _table().get(query.id == supplier_id)
    if result is None:
        return None
    return result


def list_all(
    country: str | None = None,
    category: str | None = None,
) -> list[SupplierRecord]:
    records: list[SupplierRecord] = _table().all()

    if country is not None:
        records = [record for record in records if record["country"] == country]

    if category is not None:
        records = [
            record for record in records if category in record["categories"]
        ]

    return sorted(records, key=lambda record: record["id"])


def find_by_name_country(name: str, country: str) -> SupplierRecord | None:
    query = Query()
    result = _table().get((query.name == name) & (query.country == country))
    if result is None:
        return None
    return result


def update(supplier_id: int, fields: dict[str, Any]) -> SupplierRecord | None:
    query = Query()
    table = _table()
    if not table.contains(query.id == supplier_id):
        return None

    table.update(fields, query.id == supplier_id)
    return get(supplier_id)


def delete(supplier_id: int) -> bool:
    query = Query()
    table = _table()
    removed = table.remove(query.id == supplier_id)
    return len(removed) > 0
