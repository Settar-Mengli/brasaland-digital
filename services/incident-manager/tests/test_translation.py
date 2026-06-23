from __future__ import annotations

import csv
from pathlib import Path

from incident_manager.translations import SPANISH_TO_ENGLISH

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


def _distinct_non_empty_descriptions(csv_path: Path) -> set[str]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {
            row["description"].strip()
            for row in reader
            if row["description"].strip()
        }


def test_translation_map_covers_every_distinct_fixture_description() -> None:
    descriptions = _distinct_non_empty_descriptions(FIXTURE_PATH)
    missing = sorted(description for description in descriptions if description not in SPANISH_TO_ENGLISH)

    assert missing == []
    assert len(descriptions) == 33


def test_translation_map_values_are_english_ascii_safe() -> None:
    spanish_markers = ("ñ", "á", "é", "í", "ó", "ú", "ü", "¿", "¡")
    for spanish, english in SPANISH_TO_ENGLISH.items():
        assert spanish
        assert english
        assert not any(marker in english for marker in spanish_markers)


def test_empty_fixture_description_is_not_in_translation_map() -> None:
    assert "" not in SPANISH_TO_ENGLISH
