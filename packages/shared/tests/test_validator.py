from brasaland_shared.incident_validator import validate_incident_fields


def _valid_data(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "Grill temperature issue",
        "description": "Customer reported undercooked steak at table 12",
        "category": "QUEJA_CLIENTE",
        "status": "open",
        "origin": "customer",
        "branch": "COL-01",
    }
    base.update(overrides)
    return base


def _error_fields(errors: list[dict[str, str]]) -> set[str]:
    return {error["field"] for error in errors}


def test_title_missing() -> None:
    errors = validate_incident_fields(_valid_data(title=""))
    assert any(error["field"] == "title" for error in errors)
    assert any(error["message"] == "title is required" for error in errors)


def test_description_missing() -> None:
    errors = validate_incident_fields(_valid_data(description="   "))
    assert any(error["field"] == "description" for error in errors)
    assert any(error["message"] == "description is required" for error in errors)


def test_category_missing() -> None:
    errors = validate_incident_fields(_valid_data(category=""))
    assert any(error["field"] == "category" for error in errors)
    assert any(error["message"] == "category is required" for error in errors)


def test_status_missing() -> None:
    errors = validate_incident_fields(_valid_data(status=""))
    assert any(error["field"] == "status" for error in errors)
    assert any(error["message"] == "status is required" for error in errors)


def test_origin_missing() -> None:
    errors = validate_incident_fields(_valid_data(origin=""))
    assert any(error["field"] == "origin" for error in errors)
    assert any(error["message"] == "origin is required" for error in errors)


def test_branch_missing() -> None:
    errors = validate_incident_fields(_valid_data(branch=""))
    assert any(error["field"] == "branch" for error in errors)
    assert any(error["message"] == "branch is required" for error in errors)


def test_category_invalid() -> None:
    errors = validate_incident_fields(_valid_data(category="UNKNOWN"))
    assert errors == [
        {
            "field": "category",
            "message": "category must be one of the allowed values",
        }
    ]


def test_status_invalid() -> None:
    errors = validate_incident_fields(_valid_data(status="frozen"))
    assert errors == [
        {
            "field": "status",
            "message": "status must be one of the allowed values",
        }
    ]


def test_origin_invalid() -> None:
    errors = validate_incident_fields(_valid_data(origin="vendor"))
    assert errors == [
        {
            "field": "origin",
            "message": "origin must be one of the allowed values",
        }
    ]


def test_branch_invalid() -> None:
    errors = validate_incident_fields(_valid_data(branch="COL-99"))
    assert errors == [
        {
            "field": "branch",
            "message": "branch must be one of the allowed values",
        }
    ]


def test_whitespace_only_values_treated_as_missing() -> None:
    errors = validate_incident_fields(
        _valid_data(
            title="   ",
            description="\t",
            category=" ",
            status="  ",
            origin="\n",
            branch="   ",
        )
    )

    assert _error_fields(errors) == {
        "title",
        "description",
        "category",
        "status",
        "origin",
        "branch",
    }


def test_multiple_errors_accumulate_without_short_circuit() -> None:
    errors = validate_incident_fields(
        {
            "title": "",
            "description": "",
            "category": "NOT_A_CATEGORY",
            "status": "frozen",
            "origin": "vendor",
            "branch": "COL-99",
        }
    )

    assert _error_fields(errors) == {
        "title",
        "description",
        "category",
        "status",
        "origin",
        "branch",
    }
    assert len(errors) == 6


def test_fully_valid_dict_returns_empty_list() -> None:
    assert validate_incident_fields(_valid_data()) == []
