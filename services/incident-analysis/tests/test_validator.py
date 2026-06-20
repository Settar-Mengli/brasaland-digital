from incident_analysis.constants import (
    RULE_CERRADO_MISSING_SCORE,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_INVALID_LOCATION,
    RULE_INVALID_SATISFACTION_SCORE,
    RULE_MISSING_REPORTER,
)
from incident_analysis.types import IncidentRow
from incident_analysis.validator import validate_record


def _row(**overrides: str) -> IncidentRow:
    base: IncidentRow = {
        "incident_id": "BRS-000001",
        "date": "2024-01-01",
        "location_id": "COL-01",
        "category": "QUEJA_CLIENTE",
        "description": "Valid description text",
        "status": "ABIERTO",
        "customer_id": "",
        "satisfaction_score": "",
        "reporter_id": "MGR-01",
    }
    base.update(overrides)
    return base


def test_invalid_location_rule() -> None:
    outcome = validate_record(_row(location_id=""))
    assert RULE_INVALID_LOCATION in outcome.failed_rules


def test_invalid_category_rule() -> None:
    outcome = validate_record(_row(category="UNKNOWN"))
    assert RULE_INVALID_CATEGORY in outcome.failed_rules


def test_invalid_description_rule() -> None:
    outcome = validate_record(_row(description="abc"))
    assert RULE_INVALID_DESCRIPTION in outcome.failed_rules


def test_missing_reporter_rule() -> None:
    outcome = validate_record(_row(reporter_id=""))
    assert RULE_MISSING_REPORTER in outcome.failed_rules


def test_cerrado_missing_score_rule() -> None:
    outcome = validate_record(_row(status="CERRADO", satisfaction_score=""))
    assert RULE_CERRADO_MISSING_SCORE in outcome.failed_rules


def test_invalid_satisfaction_score_rule() -> None:
    outcome = validate_record(_row(satisfaction_score="3.5"))
    assert RULE_INVALID_SATISFACTION_SCORE in outcome.failed_rules


def test_multiple_rules_accumulate_without_short_circuit() -> None:
    outcome = validate_record(
        _row(
            location_id="",
            category="",
            description="",
            reporter_id="",
            status="CERRADO",
            satisfaction_score="",
        )
    )

    assert outcome.is_valid is False
    assert set(outcome.failed_rules) == {
        RULE_INVALID_LOCATION,
        RULE_INVALID_CATEGORY,
        RULE_INVALID_DESCRIPTION,
        RULE_MISSING_REPORTER,
        RULE_CERRADO_MISSING_SCORE,
    }


def test_valid_record_has_no_failed_rules() -> None:
    outcome = validate_record(_row())
    assert outcome.is_valid is True
    assert outcome.failed_rules == ()
