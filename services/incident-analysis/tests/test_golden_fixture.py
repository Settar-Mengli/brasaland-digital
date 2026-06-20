from pathlib import Path

from incident_analysis import run_analysis
from incident_analysis.constants import (
    RULE_CERRADO_MISSING_SCORE,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_INVALID_LOCATION,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


def test_golden_fixture_matches_expected_summary() -> None:
    result = run_analysis(FIXTURE_PATH)

    assert result.totals.total == 100
    assert result.totals.valid == 96
    assert result.totals.invalid == 4

    assert result.by_category == {
        "QUEJA_CLIENTE": 29,
        "EQUIPAMIENTO": 17,
        "ABASTECIMIENTO": 22,
        "CALIDAD_ALIMENTO": 19,
        "PERSONAL": 9,
    }

    assert result.by_status == {
        "ABIERTO": 32,
        "CERRADO": 50,
        "DESCARTADO": 14,
    }

    assert result.average_satisfaction_closed == 3.46

    assert result.satisfaction_distribution == {1: 4, 2: 6, 3: 12, 4: 19, 5: 9}
    assert sum(result.satisfaction_distribution.values()) == 50

    assert result.invalid_count_by_rule[RULE_INVALID_LOCATION] == 1
    assert result.invalid_count_by_rule[RULE_INVALID_CATEGORY] == 1
    assert result.invalid_count_by_rule[RULE_INVALID_DESCRIPTION] == 1
    assert result.invalid_count_by_rule[RULE_CERRADO_MISSING_SCORE] == 1

    assert len(result.invalid_records) == 4


def test_golden_fixture_path_exists() -> None:
    assert FIXTURE_PATH.is_file(), "Golden fixture CSV is missing"
