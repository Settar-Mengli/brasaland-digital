from brasaland_shared.constants import (
    REQUIRED_FIELDS,
    VALID_BRANCHES,
    VALID_CATEGORIES,
    VALID_ORIGINS,
    VALID_STATUSES,
)
from brasaland_shared.types import FieldError


def _stripped_value(data: dict[str, object], field_name: str) -> str:
    raw = data.get(field_name, "")
    if raw is None:
        return ""
    return str(raw).strip()


def validate_incident_fields(data: dict[str, object]) -> list[FieldError]:
    errors: list[FieldError] = []

    for field_name in REQUIRED_FIELDS:
        if not _stripped_value(data, field_name):
            errors.append({"field": field_name, "message": f"{field_name} is required"})

    category = _stripped_value(data, "category")
    if category and category not in VALID_CATEGORIES:
        errors.append(
            {
                "field": "category",
                "message": "category must be one of the allowed values",
            }
        )

    status = _stripped_value(data, "status")
    if status and status not in VALID_STATUSES:
        errors.append(
            {
                "field": "status",
                "message": "status must be one of the allowed values",
            }
        )

    origin = _stripped_value(data, "origin")
    if origin and origin not in VALID_ORIGINS:
        errors.append(
            {
                "field": "origin",
                "message": "origin must be one of the allowed values",
            }
        )

    branch = _stripped_value(data, "branch")
    if branch and branch not in VALID_BRANCHES:
        errors.append(
            {
                "field": "branch",
                "message": "branch must be one of the allowed values",
            }
        )

    return errors
