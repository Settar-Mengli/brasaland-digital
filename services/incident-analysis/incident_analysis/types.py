from dataclasses import dataclass, field
from typing import TypedDict


class IncidentRow(TypedDict):
    incident_id: str
    date: str
    location_id: str
    category: str
    description: str
    status: str
    customer_id: str
    satisfaction_score: str
    reporter_id: str


@dataclass(frozen=True)
class ValidationOutcome:
    is_valid: bool
    failed_rules: tuple[str, ...]


@dataclass(frozen=True)
class RecordResult:
    row: IncidentRow
    row_number: int
    outcome: ValidationOutcome


@dataclass(frozen=True)
class Totals:
    valid: int
    invalid: int
    total: int


@dataclass(frozen=True)
class InvalidRecord:
    incident_id: str
    failed_rules: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    totals: Totals
    by_category: dict[str, int]
    by_status: dict[str, int]
    average_satisfaction_closed: float | None
    invalid_records: tuple[InvalidRecord, ...]
    invalid_count_by_rule: dict[str, int] = field(default_factory=dict)
    satisfaction_distribution: dict[int, int] = field(default_factory=dict)
