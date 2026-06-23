REQUIRED_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "category",
    "status",
    "origin",
    "branch",
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
    {"open", "in_progress", "resolved", "discarded"}
)

VALID_ORIGINS: frozenset[str] = frozenset({"customer", "branch", "internal"})

VALID_BRANCHES: frozenset[str] = frozenset(
    [f"COL-{index:02d}" for index in range(1, 11)]
    + [f"FLA-{index:02d}" for index in range(1, 5)]
    + ["Central"]
)
