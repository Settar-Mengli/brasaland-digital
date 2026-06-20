import csv
import io

from incident_analysis.constants import VALID_CATEGORIES, VALID_STATUSES
from incident_analysis.types import AnalysisResult


def _format_percentage(value: int, denominator: int) -> str:
    if denominator == 0:
        return ""
    percentage = (value / denominator) * 100
    return f"{percentage:.1f}"


def summary_to_export_rows(
    result: AnalysisResult,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    valid_count = result.totals.valid

    rows.append({"metric": "total_records", "value": str(result.totals.total), "percentage": ""})
    rows.append({"metric": "valid_records", "value": str(result.totals.valid), "percentage": ""})
    rows.append(
        {"metric": "invalid_records", "value": str(result.totals.invalid), "percentage": ""}
    )

    for category in sorted(VALID_CATEGORIES):
        count = result.by_category.get(category, 0)
        rows.append(
            {
                "metric": f"category_{category}",
                "value": str(count),
                "percentage": _format_percentage(count, valid_count),
            }
        )

    for status in sorted(VALID_STATUSES):
        count = result.by_status.get(status, 0)
        rows.append(
            {
                "metric": f"status_{status}",
                "value": str(count),
                "percentage": _format_percentage(count, valid_count),
            }
        )

    average_value = (
        f"{result.average_satisfaction_closed:.2f}"
        if result.average_satisfaction_closed is not None
        else ""
    )
    rows.append(
        {
            "metric": "average_satisfaction_closed",
            "value": average_value,
            "percentage": "",
        }
    )

    return rows


def export_summary_csv(result: AnalysisResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["metric", "value", "percentage"])
    writer.writeheader()
    writer.writerows(summary_to_export_rows(result))
    return buffer.getvalue()
