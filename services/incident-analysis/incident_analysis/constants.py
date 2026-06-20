REQUIRED_COLUMNS: tuple[str, ...] = (
    "incident_id",
    "date",
    "location_id",
    "category",
    "description",
    "status",
    "customer_id",
    "satisfaction_score",
    "reporter_id",
)

VALID_LOCATION_IDS: frozenset[str] = frozenset(
    [f"COL-{index:02d}" for index in range(1, 11)]
    + [f"FLA-{index:02d}" for index in range(1, 5)]
)

VALID_CATEGORIES: frozenset[str] = frozenset(
    {
        "QUEJA_CLIENTE",
        "EQUIPAMIENTO",
        "ABASTECIMIENTO",
        "CALIDAD_ALIMENTO",
        "PERSONAL",
    }
)

VALID_STATUSES: frozenset[str] = frozenset(
    {"ABIERTO", "CERRADO", "DESCARTADO"}
)

RULE_INVALID_LOCATION = "invalid_location"
RULE_INVALID_CATEGORY = "invalid_category"
RULE_INVALID_DESCRIPTION = "invalid_description"
RULE_MISSING_REPORTER = "missing_reporter"
RULE_CERRADO_MISSING_SCORE = "cerrado_missing_score"
RULE_INVALID_SATISFACTION_SCORE = "invalid_satisfaction_score"

VALIDATION_RULE_IDS: tuple[str, ...] = (
    RULE_INVALID_LOCATION,
    RULE_INVALID_CATEGORY,
    RULE_INVALID_DESCRIPTION,
    RULE_MISSING_REPORTER,
    RULE_CERRADO_MISSING_SCORE,
    RULE_INVALID_SATISFACTION_SCORE,
)
