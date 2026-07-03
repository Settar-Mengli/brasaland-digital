from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from incident_manager.database import ensure_schema
from incident_manager.seed_mapping import load_mapped_rows_from_csv
from incident_manager.service import seed_batch

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "incident-analysis"
    / "incidents-brasaland.csv"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed incidents from historical CSV export.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(DEFAULT_CSV_PATH),
        help="Path to incidents CSV (default: services/incident-analysis/incidents-brasaland.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        print(f"CSV file not found: {csv_path}", file=sys.stderr)
        raise SystemExit(1)

    rows = load_mapped_rows_from_csv(csv_path)
    ensure_schema()
    report = seed_batch(rows)

    print(f"Inserted: {report.inserted}")
    print(f"Skipped (duplicate): {report.skipped_duplicate}")
    print(f"Rejected: {len(report.rejected)}")

    for rejected in report.rejected:
        reason_text = "; ".join(rejected.reasons)
        print(f"  - {rejected.source_incident_id}: {reason_text}")


if __name__ == "__main__":
    main()
