from __future__ import annotations

from datetime import datetime, timezone

from brasaland_shared import (
    FieldError,
    VALID_BRANCHES,
    VALID_CATEGORIES,
    VALID_ORIGINS,
    VALID_STATUSES,
    validate_incident_fields,
    validate_transition,
)

from incident_manager.repository import (
    count_all,
    find_by_source_incident_id,
    get,
    insert,
    list_with_filters,
    update_status_fields,
)
from incident_manager.types import (
    IncidentCreateInput,
    IncidentRecord,
    IncidentSeedInput,
    IncidentSummary,
    RejectedSeedRow,
    SeedReport,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validation_payload(row: IncidentSeedInput) -> dict[str, object]:
    return {
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "status": row["status"],
        "origin": row["origin"],
        "branch": row["branch"],
    }


def _empty_summary() -> IncidentSummary:
    return {
        "total": 0,
        "by_status": {},
        "by_category": {},
        "by_origin": {},
        "by_branch": {},
    }


def seed_batch(rows: list[IncidentSeedInput]) -> SeedReport:
    inserted_count = 0
    skipped_duplicate_count = 0
    rejected_rows: list[RejectedSeedRow] = []

    for row in rows:
        field_errors = validate_incident_fields(_validation_payload(row))
        if field_errors:
            rejected_rows.append(
                RejectedSeedRow(
                    source_incident_id=row["source_incident_id"],
                    reasons=tuple(
                        f"{error['field']}: {error['message']}" for error in field_errors
                    ),
                )
            )
            continue

        if find_by_source_incident_id(row["source_incident_id"]) is not None:
            skipped_duplicate_count += 1
            continue

        insert(dict(row))
        inserted_count += 1

    return SeedReport(
        inserted=inserted_count,
        skipped_duplicate=skipped_duplicate_count,
        rejected=tuple(rejected_rows),
    )


def incident_count() -> int:
    return count_all()


def create_incident(data: IncidentCreateInput) -> tuple[IncidentRecord | None, list[FieldError]]:
    payload: dict[str, object] = {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "category": data.get("category", ""),
        "status": data.get("status") or "open",
        "origin": data.get("origin", ""),
        "branch": data.get("branch", ""),
    }
    field_errors = validate_incident_fields(payload)
    if field_errors:
        return None, field_errors

    timestamp = _utc_now_iso()
    record = insert(
        {
            "title": str(payload["title"]),
            "description": str(payload["description"]),
            "category": str(payload["category"]),
            "status": str(payload["status"]),
            "origin": str(payload["origin"]),
            "branch": str(payload["branch"]),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    return record, []


def list_incidents(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[IncidentRecord]:
    return list_with_filters(
        status=status,
        origin=origin,
        branch=branch,
        category=category,
    )


def get_incident(incident_id: int) -> IncidentRecord | None:
    return get(incident_id)


def build_summary() -> IncidentSummary:
    records = list_with_filters()
    if not records:
        return _empty_summary()

    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_origin: dict[str, int] = {}
    by_branch: dict[str, int] = {}

    for record in records:
        by_status[record["status"]] = by_status.get(record["status"], 0) + 1
        by_category[record["category"]] = by_category.get(record["category"], 0) + 1
        by_origin[record["origin"]] = by_origin.get(record["origin"], 0) + 1
        by_branch[record["branch"]] = by_branch.get(record["branch"], 0) + 1

    return {
        "total": len(records),
        "by_status": by_status,
        "by_category": by_category,
        "by_origin": by_origin,
        "by_branch": by_branch,
    }


def update_incident_status(
    incident_id: int,
    target_status: str,
) -> tuple[IncidentRecord | None, str | None]:
    record = get(incident_id)
    if record is None:
        return None, None

    transition = validate_transition(record["status"], target_status)
    if not transition.is_allowed:
        return record, transition.message

    updated = update_status_fields(incident_id, target_status, _utc_now_iso())
    return updated, None


def validate_list_filters(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[FieldError]:
    errors: list[FieldError] = []

    if status is not None and status not in VALID_STATUSES:
        errors.append(
            {
                "field": "status",
                "message": "status must be one of the allowed values",
            }
        )

    if origin is not None and origin not in VALID_ORIGINS:
        errors.append(
            {
                "field": "origin",
                "message": "origin must be one of the allowed values",
            }
        )

    if branch is not None and branch not in VALID_BRANCHES:
        errors.append(
            {
                "field": "branch",
                "message": "branch must be one of the allowed values",
            }
        )

    if category is not None and category not in VALID_CATEGORIES:
        errors.append(
            {
                "field": "category",
                "message": "category must be one of the allowed values",
            }
        )

    return errors
