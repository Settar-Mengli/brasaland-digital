from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class IncidentRecord(TypedDict):
    id: int
    source_incident_id: str
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class IncidentSeedInput(TypedDict):
    source_incident_id: str
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class IncidentCreateInput(TypedDict, total=False):
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str


class IncidentSummary(TypedDict):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_origin: dict[str, int]
    by_branch: dict[str, int]


@dataclass(frozen=True)
class RejectedSeedRow:
    source_incident_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SeedReport:
    inserted: int
    skipped_duplicate: int
    rejected: tuple[RejectedSeedRow, ...]
