from incident_analysis.constants import VALID_CATEGORIES, VALID_STATUSES
from incident_analysis.types import AnalysisResult, RecordResult, Totals
from incident_analysis.validator import count_invalid_by_rule


def _parse_score_value(raw: str) -> int | None:
    stripped = raw.strip()
    if not stripped or "." in stripped:
        return None
    try:
        value = int(stripped)
    except ValueError:
        return None
    if 1 <= value <= 5:
        return value
    return None


def count_totals(record_results: list[RecordResult]) -> Totals:
    valid = sum(1 for record in record_results if record.outcome.is_valid)
    invalid = len(record_results) - valid
    return Totals(valid=valid, invalid=invalid, total=len(record_results))


def count_by_category(valid_records: list[RecordResult]) -> dict[str, int]:
    counts = {category: 0 for category in sorted(VALID_CATEGORIES)}
    for record in valid_records:
        category = record.row["category"]
        counts[category] = counts.get(category, 0) + 1
    return counts


def count_by_status(valid_records: list[RecordResult]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for record in valid_records:
        status = record.row["status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def average_satisfaction_closed(
    valid_records: list[RecordResult],
) -> float | None:
    scores: list[int] = []
    for record in valid_records:
        if record.row["status"] != "CERRADO":
            continue
        score = _parse_score_value(record.row["satisfaction_score"])
        if score is not None:
            scores.append(score)

    if not scores:
        return None

    average = sum(scores) / len(scores)
    return round(average, 2)


def build_summary(record_results: list[RecordResult]) -> AnalysisResult:
    valid_records = [
        record for record in record_results if record.outcome.is_valid
    ]
    totals = count_totals(record_results)

    return AnalysisResult(
        totals=totals,
        by_category=count_by_category(valid_records),
        by_status=count_by_status(valid_records),
        average_satisfaction_closed=average_satisfaction_closed(valid_records),
        invalid_records=tuple(),
        invalid_count_by_rule=count_invalid_by_rule(record_results),
    )
