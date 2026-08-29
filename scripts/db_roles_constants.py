"""Shared constants for brasaland DB runtime roles, grants, and RLS verification."""

from __future__ import annotations

RUNTIME_ROLES: tuple[str, ...] = (
    "brasaland_inventory",
    "brasaland_telemetry",
    "brasaland_incident",
    "brasaland_rfp",
    "brasaland_reporting",
)

PUBLIC_APP_TABLES: tuple[str, ...] = (
    "ingredient",
    "ingrediententry",
    "ingredientexit",
    "incident",
    "telemetry_events",
    "ticket",
    "rfp_metadata",
    "department_section",
    "final_document",
)

REPORTING_APP_TABLES: tuple[str, ...] = (
    "weekly_location_performance",
    "pipeline_runs",
    "job_runs",
    "task_dead_letters",
)

# Tables that must have RLS enabled + FORCE after apply.
RLS_PUBLIC_TABLES: tuple[str, ...] = PUBLIC_APP_TABLES
RLS_REPORTING_TABLES: tuple[str, ...] = REPORTING_APP_TABLES

# Privilege matrix: role -> (schema, table) -> privileges
TABLE_GRANTS: dict[str, dict[tuple[str, str], tuple[str, ...]]] = {
    "brasaland_inventory": {
        ("public", "ingredient"): ("SELECT", "INSERT", "UPDATE"),
        ("public", "ingrediententry"): ("SELECT", "INSERT", "UPDATE"),
        ("public", "ingredientexit"): ("SELECT", "INSERT", "UPDATE"),
    },
    "brasaland_telemetry": {
        ("public", "telemetry_events"): ("SELECT", "INSERT"),
    },
    "brasaland_incident": {
        ("public", "incident"): ("SELECT", "INSERT", "UPDATE"),
    },
    "brasaland_rfp": {
        ("public", "ticket"): ("SELECT", "INSERT", "UPDATE"),
        ("public", "rfp_metadata"): ("SELECT", "INSERT", "UPDATE"),
        ("public", "department_section"): ("SELECT", "INSERT", "UPDATE"),
        ("public", "final_document"): ("SELECT", "INSERT", "UPDATE"),
    },
    "brasaland_reporting": {
        ("reporting", "weekly_location_performance"): (
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
        ),
        ("reporting", "pipeline_runs"): ("SELECT", "INSERT", "UPDATE", "DELETE"),
        ("reporting", "job_runs"): ("SELECT", "INSERT", "UPDATE", "DELETE"),
        ("reporting", "task_dead_letters"): ("SELECT", "INSERT", "UPDATE", "DELETE"),
        ("public", "telemetry_events"): ("SELECT",),
    },
}

# Cross-service denial smoke: role -> (schema, table) that must NOT be readable.
CROSS_DENY_READS: dict[str, tuple[tuple[str, str], ...]] = {
    "brasaland_inventory": (("public", "telemetry_events"), ("public", "incident")),
    "brasaland_telemetry": (("public", "ingredient"),),
    "brasaland_incident": (("public", "telemetry_events"),),
    "brasaland_rfp": (("public", "ingredient"),),
    "brasaland_reporting": (("public", "ingredient"),),
}

POLICY_SUFFIX: dict[tuple[str, str], str] = {
    ("public", "ingredient"): "inventory_ingredient_all",
    ("public", "ingrediententry"): "inventory_ingrediententry_all",
    ("public", "ingredientexit"): "inventory_ingredientexit_all",
    ("public", "telemetry_events"): "telemetry_events_all",
    ("public", "incident"): "incident_all",
    ("public", "ticket"): "rfp_ticket_all",
    ("public", "rfp_metadata"): "rfp_metadata_all",
    ("public", "department_section"): "rfp_department_section_all",
    ("public", "final_document"): "rfp_final_document_all",
    ("reporting", "weekly_location_performance"): "reporting_weekly_location_performance_all",
    ("reporting", "pipeline_runs"): "reporting_pipeline_runs_all",
    ("reporting", "job_runs"): "reporting_job_runs_all",
    ("reporting", "task_dead_letters"): "reporting_task_dead_letters_all",
}

REPORTING_TELEMETRY_READ_POLICY = "reporting_telemetry_events_read"

DEFAULT_CI_ROLE_PASSWORD = "ci_brasaland_runtime_role_password"
