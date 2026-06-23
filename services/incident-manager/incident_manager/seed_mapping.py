from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from incident_manager.types import IncidentSeedInput

_CSV_STATUS_TO_INCIDENT_STATUS: dict[str, str] = {
    "ABIERTO": "open",
    "CERRADO": "resolved",
    "DESCARTADO": "discarded",
}


def csv_date_to_iso_midnight_utc(date_value: str) -> str:
    parsed = datetime.strptime(date_value.strip(), "%Y-%m-%d")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def map_csv_row(row: dict[str, str]) -> IncidentSeedInput:
    incident_id = row["incident_id"].strip()
    description = row["description"].strip()
    mapped_status = _CSV_STATUS_TO_INCIDENT_STATUS.get(row["status"].strip(), row["status"].strip())
    timestamp = csv_date_to_iso_midnight_utc(row["date"])

    return {
        "source_incident_id": incident_id,
        "title": f"{incident_id}: {description[:60]}",
        "description": description,
        "category": row["category"].strip(),
        "status": mapped_status,
        "origin": "customer",
        "branch": row["location_id"].strip(),
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def load_mapped_rows_from_csv(csv_path: Path) -> list[IncidentSeedInput]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [map_csv_row(row) for row in reader]
