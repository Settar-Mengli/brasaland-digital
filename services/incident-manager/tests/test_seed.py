from __future__ import annotations

from pathlib import Path

from incident_manager.repository import list_all
from incident_manager.seed_mapping import load_mapped_rows_from_csv
from incident_manager.service import incident_count, seed_batch

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


def test_seed_inserts_exactly_ninety_seven_rows() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)
    report = seed_batch(rows)

    assert report.inserted == 97
    assert report.skipped_duplicate == 0
    assert len(report.rejected) == 3
    assert incident_count() == 97


def test_seed_rejects_expected_incident_ids_with_reasons() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)
    report = seed_batch(rows)

    rejected_by_id = {
        rejected.source_incident_id: rejected.reasons for rejected in report.rejected
    }

    assert set(rejected_by_id) == {"BRS-000044", "BRS-000049", "BRS-000079"}
    assert "branch: branch is required" in rejected_by_id["BRS-000044"]
    assert "category: category is required" in rejected_by_id["BRS-000049"]
    assert "description: description is required" in rejected_by_id["BRS-000079"]


def test_seed_batch_is_idempotent() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)

    first_report = seed_batch(rows)
    second_report = seed_batch(rows)

    assert first_report.inserted == 97
    assert second_report.inserted == 0
    assert second_report.skipped_duplicate == 97
    assert incident_count() == 97


def test_seeded_rows_have_customer_origin() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)
    seed_batch(rows)

    assert all(record["origin"] == "customer" for record in list_all())


def test_cerrado_csv_row_maps_to_resolved_status() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)
    seed_batch(rows)

    seeded = next(
        record for record in list_all() if record["source_incident_id"] == "BRS-000001"
    )

    assert seeded["status"] == "resolved"


def test_brs_000086_is_inserted_despite_missing_satisfaction_score() -> None:
    rows = load_mapped_rows_from_csv(FIXTURE_PATH)
    seed_batch(rows)

    seeded_ids = {record["source_incident_id"] for record in list_all()}

    assert "BRS-000086" in seeded_ids
