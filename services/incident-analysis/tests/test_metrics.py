from incident_analysis.metrics import average_satisfaction_closed, build_summary
from incident_analysis.types import IncidentRow, RecordResult, ValidationOutcome
from incident_analysis.validator import validate_record


def _record(**overrides: str) -> RecordResult:
    row: IncidentRow = {
        "incident_id": "BRS-000001",
        "date": "2024-01-01",
        "location_id": "COL-01",
        "category": "QUEJA_CLIENTE",
        "description": "Valid description text",
        "status": "ABIERTO",
        "customer_id": "",
        "satisfaction_score": "",
        "reporter_id": "MGR-01",
    }
    row.update(overrides)
    return RecordResult(row=row, row_number=2, outcome=validate_record(row))


def test_average_satisfaction_closed_returns_none_without_scored_cases() -> None:
    records = [
        _record(status="ABIERTO"),
        _record(status="CERRADO", satisfaction_score=""),
    ]
    valid_records = [record for record in records if record.outcome.is_valid]

    assert average_satisfaction_closed(valid_records) is None


def test_average_satisfaction_closed_rounds_to_two_decimals() -> None:
    records = [
        _record(status="CERRADO", satisfaction_score="1"),
        _record(status="CERRADO", satisfaction_score="2"),
        _record(status="CERRADO", satisfaction_score="3"),
    ]
    valid_records = [record for record in records if record.outcome.is_valid]

    assert average_satisfaction_closed(valid_records) == 2.0


def test_build_summary_excludes_invalid_records_from_category_counts() -> None:
    valid = _record(category="QUEJA_CLIENTE")
    invalid = _record(category="QUEJA_CLIENTE", location_id="")
    invalid = RecordResult(
        row=invalid.row,
        row_number=3,
        outcome=validate_record(invalid.row),
    )

    summary = build_summary([valid, invalid])

    assert summary.totals.valid == 1
    assert summary.totals.invalid == 1
    assert summary.by_category["QUEJA_CLIENTE"] == 1
