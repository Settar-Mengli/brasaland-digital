from __future__ import annotations

from brasaland_shared import validate_incident_fields

from incident_manager.repository import count_all, find_by_source_incident_id, insert
from incident_manager.types import IncidentSeedInput, RejectedSeedRow, SeedReport


def _validation_payload(row: IncidentSeedInput) -> dict[str, object]:
    return {
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "status": row["status"],
        "origin": row["origin"],
        "branch": row["branch"],
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
