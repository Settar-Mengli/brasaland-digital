from incident_analysis.constants import (
    RULE_CERRADO_MISSING_SCORE,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_INVALID_LOCATION,
    RULE_INVALID_SATISFACTION_SCORE,
    RULE_MISSING_REPORTER,
    VALID_CATEGORIES,
    VALID_LOCATION_IDS,
    VALID_STATUSES,
    VALIDATION_RULE_IDS,
)
from incident_analysis.types import IncidentRow, RecordResult, ValidationOutcome


def _field_value(row: IncidentRow, field_name: str) -> str:
    return row[field_name].strip()


def _parse_satisfaction_score(raw: str) -> tuple[bool, bool]:
    stripped = raw.strip()
    if not stripped:
        return False, False

    if "." in stripped:
        try:
            numeric = float(stripped)
        except ValueError:
            return True, False
        if numeric != int(numeric):
            return True, False

    try:
        value = int(stripped)
    except ValueError:
        return True, False

    return True, 1 <= value <= 5


def validate_record(row: IncidentRow) -> ValidationOutcome:
    failed_rules: list[str] = []

    location_id = _field_value(row, "location_id")
    if not location_id or location_id not in VALID_LOCATION_IDS:
        failed_rules.append(RULE_INVALID_LOCATION)

    category = _field_value(row, "category")
    if not category or category not in VALID_CATEGORIES:
        failed_rules.append(RULE_INVALID_CATEGORY)

    description = _field_value(row, "description")
    if not description or len(description) < 5:
        failed_rules.append(RULE_INVALID_DESCRIPTION)

    reporter_id = _field_value(row, "reporter_id")
    if not reporter_id:
        failed_rules.append(RULE_MISSING_REPORTER)

    status = _field_value(row, "status")
    score_present, score_valid = _parse_satisfaction_score(
        row["satisfaction_score"]
    )

    if status == "CERRADO" and not score_present:
        failed_rules.append(RULE_CERRADO_MISSING_SCORE)

    if score_present and not score_valid:
        failed_rules.append(RULE_INVALID_SATISFACTION_SCORE)

    if status and status not in VALID_STATUSES:
        pass

    return ValidationOutcome(
        is_valid=len(failed_rules) == 0,
        failed_rules=tuple(failed_rules),
    )


def validate_all(rows: list[IncidentRow]) -> list[RecordResult]:
    return [
        RecordResult(
            row=row,
            row_number=index + 2,
            outcome=validate_record(row),
        )
        for index, row in enumerate(rows)
    ]


def count_invalid_by_rule(record_results: list[RecordResult]) -> dict[str, int]:
    counts = {rule_id: 0 for rule_id in VALIDATION_RULE_IDS}
    for record in record_results:
        if record.outcome.is_valid:
            continue
        for rule_id in record.outcome.failed_rules:
            counts[rule_id] = counts.get(rule_id, 0) + 1
    return counts
