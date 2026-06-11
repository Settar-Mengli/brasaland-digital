import csv
from io import TextIOWrapper
from pathlib import Path
from typing import BinaryIO, TextIO

from incident_analysis.constants import REQUIRED_COLUMNS
from incident_analysis.types import IncidentRow

STRING_FIELDS: tuple[str, ...] = REQUIRED_COLUMNS


class CsvStructureError(ValueError):
    """Raised when the CSV header or structure is invalid."""


def _normalize_row(raw_row: dict[str, str | None]) -> IncidentRow:
    normalized: dict[str, str] = {}
    for column in STRING_FIELDS:
        value = raw_row.get(column, "")
        if value is None:
            normalized[column] = ""
        else:
            normalized[column] = value.strip()
    return IncidentRow(**normalized)


def validate_csv_structure(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise CsvStructureError("CSV file is missing a header row")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise CsvStructureError(f"CSV is missing required columns: {missing}")


def load_incidents_from_csv(
    source: str | Path | TextIO | BinaryIO,
) -> list[IncidentRow]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            return _read_csv(handle)

    if isinstance(source, BinaryIO):
        text_handle = TextIOWrapper(source, encoding="utf-8", newline="")
        return _read_csv(text_handle)

    return _read_csv(source)


def _read_csv(handle: TextIO) -> list[IncidentRow]:
    reader = csv.DictReader(handle)
    validate_csv_structure(reader.fieldnames)

    rows: list[IncidentRow] = []
    for raw_row in reader:
        if raw_row is None:
            continue
        rows.append(_normalize_row(raw_row))

    if not rows:
        raise CsvStructureError("CSV file contains no data rows")

    return rows
