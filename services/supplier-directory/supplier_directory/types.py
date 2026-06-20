from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class SupplierRecord(TypedDict):
    id: int
    name: str
    country: str
    categories: list[str]
    rate_per_unit: float
    currency: str
    rate_updated_at: str
    status: str
    contact_email: str | None
    notes: str | None


class SupplierInput(TypedDict, total=False):
    name: str
    country: str
    categories: list[str]
    rate_per_unit: float
    currency: str
    status: str
    contact_email: str | None
    notes: str | None


@dataclass(frozen=True)
class SupplierValidationError(Exception):
    failures: tuple[str, ...]

    def __str__(self) -> str:
        return "; ".join(self.failures)
