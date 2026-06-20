import pytest

from supplier_directory.types import SupplierInput, SupplierValidationError
from supplier_directory.validator import validate_rate, validate_supplier


def _base(**overrides: object) -> SupplierInput:
    data: SupplierInput = {
        "name": "Test Supplier",
        "country": "Colombia",
        "categories": ["meat"],
        "rate_per_unit": 1000.0,
        "currency": "COP",
        "status": "active",
    }
    data.update(overrides)  # type: ignore[typeddict-item]
    return data


def test_colombia_usd_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(country="Colombia", currency="USD"))

    assert "currency must be COP for country Colombia" in exc_info.value.failures


def test_usa_cop_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(
            _base(
                country="USA",
                currency="COP",
                categories=["meat"],
            )
        )

    assert "currency must be USD for country USA" in exc_info.value.failures


def test_colombia_cop_passes() -> None:
    validate_supplier(_base(country="Colombia", currency="COP"))


def test_usa_usd_passes() -> None:
    validate_supplier(
        _base(country="USA", currency="USD", categories=["meat"])
    )


def test_empty_categories_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(categories=[]))

    assert "categories must be a non-empty list" in exc_info.value.failures


def test_unknown_category_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(categories=["unknown_category"]))

    assert "categories must contain only valid category values" in exc_info.value.failures


def test_rate_zero_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(rate_per_unit=0))

    assert "rate_per_unit must be greater than 0" in exc_info.value.failures


def test_rate_negative_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(rate_per_unit=-5))

    assert "rate_per_unit must be greater than 0" in exc_info.value.failures


def test_validate_rate_zero_rejected() -> None:
    with pytest.raises(SupplierValidationError):
        validate_rate(0)


def test_validate_rate_negative_rejected() -> None:
    with pytest.raises(SupplierValidationError):
        validate_rate(-1)


def test_invalid_status_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(status="inactive"))

    assert "status must be active or suspended" in exc_info.value.failures


def test_empty_name_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(name=""))

    assert "name is required" in exc_info.value.failures


def test_whitespace_name_rejected() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(_base(name="   "))

    assert "name is required" in exc_info.value.failures


def test_duplicate_categories_deduped_on_create() -> None:
    from supplier_directory import create

    payload: SupplierInput = {
        "name": "Dedupe Supplier",
        "country": "Colombia",
        "categories": ["meat", "meat"],
        "rate_per_unit": 1000.0,
        "currency": "COP",
        "status": "active",
    }
    stored = create(payload)

    assert payload["categories"] == ["meat", "meat"]
    assert stored["categories"] == ["meat"]


def test_multiple_rules_accumulate() -> None:
    with pytest.raises(SupplierValidationError) as exc_info:
        validate_supplier(
            {
                "name": "Bad Supplier",
                "country": "Colombia",
                "categories": [],
                "rate_per_unit": -1,
                "currency": "USD",
                "status": "inactive",
            }
        )

    failures = exc_info.value.failures
    assert "currency must be COP for country Colombia" in failures
    assert "categories must be a non-empty list" in failures
    assert "rate_per_unit must be greater than 0" in failures
    assert "status must be active or suspended" in failures
    assert len(failures) == 4
