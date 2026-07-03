from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlmodel import select

from incident_manager.database import ensure_schema, get_session
from incident_manager.models import Incident
from incident_manager.types import IncidentRecord


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _to_record(incident: Incident) -> IncidentRecord:
    if incident.id is None:
        raise ValueError("incident id is required")

    return IncidentRecord(
        id=incident.id,
        source_incident_id=incident.source_incident_id,
        title=incident.title,
        description=incident.description,
        category=incident.category,
        status=incident.status,
        origin=incident.origin,
        branch=incident.branch,
        created_at=_format_timestamp(incident.created_at),
        updated_at=_format_timestamp(incident.updated_at),
    )


def insert(incident: dict[str, Any]) -> IncidentRecord:
    ensure_schema()
    provided_source = incident.get("source_incident_id")
    created_at = _parse_timestamp(str(incident["created_at"]))
    updated_at = _parse_timestamp(str(incident["updated_at"]))

    with get_session() as session:
        row = Incident(
            source_incident_id=provided_source or "__pending__",
            title=incident["title"],
            description=incident["description"],
            category=incident["category"],
            status=incident["status"],
            origin=incident["origin"],
            branch=incident["branch"],
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(row)
        session.flush()

        if not provided_source:
            row.source_incident_id = f"MANUAL-{row.id}"

        session.commit()
        session.refresh(row)
        return _to_record(row)


def find_by_source_incident_id(source_id: str) -> IncidentRecord | None:
    ensure_schema()

    with get_session() as session:
        row = session.exec(
            select(Incident).where(Incident.source_incident_id == source_id)
        ).first()
        if row is None:
            return None
        return _to_record(row)


def list_all() -> list[IncidentRecord]:
    ensure_schema()

    with get_session() as session:
        rows = session.exec(select(Incident).order_by(Incident.id)).all()
        return [_to_record(row) for row in rows]


def get(incident_id: int) -> IncidentRecord | None:
    ensure_schema()

    with get_session() as session:
        row = session.get(Incident, incident_id)
        if row is None:
            return None
        return _to_record(row)


def count_all() -> int:
    ensure_schema()

    with get_session() as session:
        count = session.exec(select(func.count()).select_from(Incident)).one()
        return int(count)


def list_with_filters(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[IncidentRecord]:
    ensure_schema()

    statement = select(Incident)

    if status is not None:
        statement = statement.where(Incident.status == status)

    if origin is not None:
        statement = statement.where(Incident.origin == origin)

    if branch is not None:
        statement = statement.where(Incident.branch == branch)

    if category is not None:
        statement = statement.where(Incident.category == category)

    statement = statement.order_by(Incident.id)

    with get_session() as session:
        rows = session.exec(statement).all()
        return [_to_record(row) for row in rows]


def update_status_fields(
    incident_id: int,
    status: str,
    updated_at: str,
) -> IncidentRecord | None:
    ensure_schema()

    with get_session() as session:
        row = session.get(Incident, incident_id)
        if row is None:
            return None

        row.status = status
        row.updated_at = _parse_timestamp(updated_at)
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_record(row)
