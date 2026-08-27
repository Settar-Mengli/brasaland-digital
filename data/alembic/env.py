"""Alembic env for the single brasaland-m5 migration history.

Loads all SQLModel table=True modules that back m5 into one SQLModel.metadata
via importlib (service projects are package=false; ordinary cross-imports fail).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlmodel import SQLModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(__file__).resolve().parents[1]

if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))


def _load_module(module_name: str, file_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


_load_module("brasaland_inventory_models", REPO_ROOT / "services" / "inventory" / "models.py")
_load_module(
    "brasaland_incident_models",
    REPO_ROOT / "services" / "incident-manager" / "incident_manager" / "models.py",
)
_load_module("brasaland_telemetry_models", REPO_ROOT / "services" / "telemetry" / "db_models.py")

import pipelines.db_models  # noqa: E402,F401
import pipelines.rfp_intake.models  # noqa: E402,F401

target_metadata = SQLModel.metadata


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required for Alembic (disposable Postgres for "
            "revision/upgrade; brasaland-m5 pooler for stamp only)."
        )
    return url


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "alembic_version":
        return False
    if type_ == "table" and getattr(object, "schema", None) not in (None, "public", "reporting"):
        return False
    return True


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS reporting"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            version_table_schema="public",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
