from pathlib import Path
from typing import BinaryIO, TextIO

from incident_analysis.loader import load_incidents_from_csv
from incident_analysis.metrics import build_summary
from incident_analysis.types import AnalysisResult, InvalidRecord
from incident_analysis.validator import validate_all


def _display_incident_id(incident_id: str, row_number: int) -> str:
    if incident_id.strip():
        return incident_id.strip()
    return f"(row {row_number})"


def run_analysis(source: str | Path | TextIO | BinaryIO) -> AnalysisResult:
    rows = load_incidents_from_csv(source)
    record_results = validate_all(rows)
    summary = build_summary(record_results)

    invalid_records = tuple(
        InvalidRecord(
            incident_id=_display_incident_id(
                record.row["incident_id"], record.row_number
            ),
            failed_rules=record.outcome.failed_rules,
        )
        for record in record_results
        if not record.outcome.is_valid
    )

    return AnalysisResult(
        totals=summary.totals,
        by_category=summary.by_category,
        by_status=summary.by_status,
        average_satisfaction_closed=summary.average_satisfaction_closed,
        invalid_records=invalid_records,
        invalid_count_by_rule=summary.invalid_count_by_rule,
    )
