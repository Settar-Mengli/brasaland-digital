from __future__ import annotations

from typing import Any

from supplier_directory.constants import (
    COUNTRY_CURRENCY,
    VALID_CATEGORIES,
    VALID_COUNTRIES,
    VALID_STATUSES,
)
from supplier_directory.types import SupplierInput, SupplierValidationError


def validate_rate(value: Any) -> None:
    failures: list[str] = []

    if not isinstance(value, (int, float)):
        failures.append("rate_per_unit must be a number")
    elif isinstance(value, bool):
        failures.append("rate_per_unit must be a number")
    elif value <= 0:
        failures.append("rate_per_unit must be greater than 0")

    if failures:
        raise SupplierValidationError(tuple(failures))


def validate_supplier(data: SupplierInput) -> None:
    failures: list[str] = []

    if not str(data.get("name", "")).strip():
        failures.append("name is required")

    country = data.get("country")
    if country not in VALID_COUNTRIES:
        failures.append("country must be Colombia or USA")

    currency = data.get("currency")
    if country in COUNTRY_CURRENCY and currency != COUNTRY_CURRENCY[country]:
        failures.append(
            f"currency must be {COUNTRY_CURRENCY[country]} for country {country}"
        )
    elif country not in COUNTRY_CURRENCY and currency not in COUNTRY_CURRENCY.values():
        failures.append("currency must match country (Colombia→COP, USA→USD)")

    categories = data.get("categories")
    if not isinstance(categories, list) or len(categories) == 0:
        failures.append("categories must be a non-empty list")
    else:
        invalid_categories = [
            category
            for category in categories
            if category not in VALID_CATEGORIES
        ]
        if invalid_categories:
            failures.append(
                "categories must contain only valid category values"
            )

    rate_per_unit = data.get("rate_per_unit")
    if not isinstance(rate_per_unit, (int, float)):
        failures.append("rate_per_unit must be a number")
    elif isinstance(rate_per_unit, bool):
        failures.append("rate_per_unit must be a number")
    elif rate_per_unit <= 0:
        failures.append("rate_per_unit must be greater than 0")

    status = data.get("status")
    if status not in VALID_STATUSES:
        failures.append("status must be active or suspended")

    if failures:
        raise SupplierValidationError(tuple(failures))
