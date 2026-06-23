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
    stored: IncidentRecord = {
        "id": incident_id,
        "source_incident_id": incident["source_incident_id"],
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
