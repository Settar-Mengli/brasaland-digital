from __future__ import annotations

from typing import Any

from tinydb import Query

from incident_manager.db import get_db
from incident_manager.types import IncidentRecord


def _table() -> Any:
    return get_db().table("incidents")


def _next_id(records: list[IncidentRecord]) -> int:
    if not records:
        return 1
    return max(record["id"] for record in records) + 1


def insert(incident: dict[str, Any]) -> IncidentRecord:
    table = _table()
    existing = table.all()
    incident_id = _next_id(existing)
    source_incident_id = incident.get("source_incident_id") or f"MANUAL-{incident_id}"
    stored: IncidentRecord = {
        "id": incident_id,
        "source_incident_id": source_incident_id,
        "title": incident["title"],
        "description": incident["description"],
        "category": incident["category"],
        "status": incident["status"],
        "origin": incident["origin"],
        "branch": incident["branch"],
        "created_at": incident["created_at"],
        "updated_at": incident["updated_at"],
    }
    table.insert(stored)
    return stored


def find_by_source_incident_id(source_id: str) -> IncidentRecord | None:
    query = Query()
    result = _table().get(query.source_incident_id == source_id)
    if result is None:
        return None
    return result


def list_all() -> list[IncidentRecord]:
    return sorted(_table().all(), key=lambda record: record["id"])


def get(incident_id: int) -> IncidentRecord | None:
    query = Query()
    result = _table().get(query.id == incident_id)
    if result is None:
        return None
    return result


def count_all() -> int:
    return len(_table().all())


def list_with_filters(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[IncidentRecord]:
    records = list_all()

    if status is not None:
        records = [record for record in records if record["status"] == status]

    if origin is not None:
        records = [record for record in records if record["origin"] == origin]

    if branch is not None:
        records = [record for record in records if record["branch"] == branch]

    if category is not None:
        records = [record for record in records if record["category"] == category]

    return records


def update_status_fields(
    incident_id: int,
    status: str,
    updated_at: str,
) -> IncidentRecord | None:
    query = Query()
    table = _table()
    if not table.contains(query.id == incident_id):
        return None

    table.update(
        {"status": status, "updated_at": updated_at},
        query.id == incident_id,
    )
    return get(incident_id)
