from __future__ import annotations

import argparse
import sys
from pathlib import Path

from incident_analysis import export_summary_csv, run_analysis
from incident_analysis.constants import (
    RULE_CERRADO_MISSING_SCORE,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_INVALID_LOCATION,
)
from incident_analysis.loader import CsvStructureError
from incident_analysis.types import AnalysisResult

RULE_LABELS: dict[str, str] = {
    RULE_INVALID_LOCATION: "Missing location_id",
    RULE_INVALID_CATEGORY: "Invalid or missing category",
    RULE_INVALID_DESCRIPTION: "Empty description",
    RULE_CERRADO_MISSING_SCORE: "Closed case, no score",
}

CATEGORY_DISPLAY_ORDER: tuple[str, ...] = (
    "QUEJA_CLIENTE",
    "EQUIPAMIENTO",
    "ABASTECIMIENTO",
    "CALIDAD_ALIMENTO",
    "PERSONAL",
)

STATUS_DISPLAY_ORDER: tuple[str, ...] = ("ABIERTO", "CERRADO", "DESCARTADO")

INVALID_RULE_DISPLAY_ORDER: tuple[str, ...] = (
    RULE_INVALID_LOCATION,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_CERRADO_MISSING_SCORE,
)

SCORE_DISPLAY_ORDER: tuple[tuple[int, str], ...] = (
    (1, "Very dissatisfied"),
    (2, "Dissatisfied"),
    (3, "Neutral"),
    (4, "Satisfied"),
    (5, "Very satisfied"),
)


def _format_percentage(value: int, denominator: int) -> str:
    if denominator == 0:
        return "N/A"
    percentage = (value / denominator) * 100
    return f"{percentage:.1f}%"


def _rule_label(rule_id: str) -> str:
    return RULE_LABELS.get(rule_id, rule_id.replace("_", " ").title())


def _print_summary(result: AnalysisResult, source_name: str) -> None:
    valid_count = result.totals.valid
    closed_count = result.by_status.get("CERRADO", 0)

    print("=" * 60)
    print("  BRASALAND — INCIDENT REPORT ANALYSIS")
    print(f"  Source file: {source_name}")
    print("=" * 60)
    print()
    print(f"TOTAL RECORDS IN FILE .......... {result.totals.total}")
    print(f"  ├─ Valid records ................ {result.totals.valid}")
    print(f"  └─ Invalid / incomplete .......... {result.totals.invalid}")
    print()
    print("INVALID RECORDS BREAKDOWN")
    for index, rule_id in enumerate(INVALID_RULE_DISPLAY_ORDER):
        count = result.invalid_count_by_rule.get(rule_id, 0)
        label = _rule_label(rule_id)
        prefix = "└─" if index == len(INVALID_RULE_DISPLAY_ORDER) - 1 else "├─"
        print(f"  {prefix} {label:<30} {count}")
    print()
    print("BREAKDOWN BY CATEGORY (valid records)")
    for index, category in enumerate(CATEGORY_DISPLAY_ORDER):
        count = result.by_category.get(category, 0)
        percentage = _format_percentage(count, valid_count)
        prefix = "└─" if index == len(CATEGORY_DISPLAY_ORDER) - 1 else "├─"
        print(f"  {prefix} {category:<24} {count:>3}  ({percentage})")
    print()
    print("BREAKDOWN BY STATUS (valid records)")
    for index, status in enumerate(STATUS_DISPLAY_ORDER):
        count = result.by_status.get(status, 0)
        percentage = _format_percentage(count, valid_count)
        prefix = "└─" if index == len(STATUS_DISPLAY_ORDER) - 1 else "├─"
        print(f"  {prefix} {status:<24} {count:>3}  ({percentage})")
    print()
    print("SATISFACTION INDEX (closed cases)")
    if result.average_satisfaction_closed is None or closed_count == 0:
        print("  Scored cases: N/A")
        print("  Average score: N/A")
    else:
        scored_count = sum(result.satisfaction_distribution.values())
        print(f"  Scored cases: {scored_count} of {closed_count}")
        print(
            f"  Average score: {result.average_satisfaction_closed:.2f} / 5.00"
        )
        for index, (score, label) in enumerate(SCORE_DISPLAY_ORDER):
            count = result.satisfaction_distribution.get(score, 0)
            prefix = "└─" if index == len(SCORE_DISPLAY_ORDER) - 1 else "├─"
            print(f"  {prefix} Score {score} ({label}) ... {count}")
    print()

    if result.invalid_records:
        print("INVALID RECORDS")
        for record in result.invalid_records:
            rules = ", ".join(_rule_label(rule_id) for rule_id in record.failed_rules)
            print(f"  ├─ {record.incident_id}: {rules}")
        print()

    print("=" * 60)


def _resolve_exit_code(error: Exception) -> int:
    if isinstance(error, FileNotFoundError):
        return 1
    if isinstance(error, CsvStructureError):
        if "no data rows" in str(error).lower():
            return 3
        return 2
    return 2


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _write_export(result: AnalysisResult, export_path: Path) -> None:
    try:
        export_path.write_text(export_summary_csv(result), encoding="utf-8")
    except OSError as error:
        raise OSError("Could not write export file") from error
    print(f"Summary exported to: {export_path.name}")


def _maybe_export_interactive(result: AnalysisResult) -> None:
    if not sys.stdin.isatty():
        return

    response = input("Export results to CSV? [y/n]: ").strip().lower()
    if response not in {"y", "yes"}:
        return

    filename = input("Export filename [results.csv]: ").strip()
    if not filename:
        filename = "results.csv"

    _write_export(result, Path(filename))


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Validate and summarize Brasaland operational incident CSV reports."
    )
    parser.add_argument(
        "csv_path",
        help="Path to the incidents CSV file",
    )
    parser.add_argument(
        "--export",
        dest="export_path",
        metavar="PATH",
        help="Write summary metrics to a CSV file at PATH",
    )
    args = parser.parse_args(argv)

    csv_path = Path(args.csv_path)
    source_name = csv_path.name

    try:
        result = run_analysis(csv_path)
    except FileNotFoundError:
        print("Error: CSV file not found", file=sys.stderr)
        return 1
    except CsvStructureError as error:
        print(f"Error: {error}", file=sys.stderr)
        return _resolve_exit_code(error)

    _print_summary(result, source_name)

    if args.export_path:
        try:
            _write_export(result, Path(args.export_path))
        except OSError:
            print("Error: Could not write export file", file=sys.stderr)
            return 4
    else:
        _maybe_export_interactive(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
