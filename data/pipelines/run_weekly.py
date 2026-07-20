"""CLI entrypoint: run the weekly location performance flow for a Monday week_start."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date


def _parse_monday(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"week-start must be YYYY-MM-DD, got {value!r}"
        ) from exc
    if parsed.weekday() != 0:
        raise argparse.ArgumentTypeError(
            f"week-start must be a Monday (ISO weekday 0), got {parsed.isoformat()} "
            f"(weekday={parsed.weekday()})"
        )
    return parsed


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description=(
            "Run weekly_location_performance_flow for an explicit Monday week_start."
        )
    )
    parser.add_argument(
        "--week-start",
        required=True,
        type=_parse_monday,
        help="ISO Monday date (YYYY-MM-DD) for the target week window",
    )
    args = parser.parse_args(argv)

    from pipelines.pipeline import weekly_location_performance_flow

    result = weekly_location_performance_flow(week_start=args.week_start)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
