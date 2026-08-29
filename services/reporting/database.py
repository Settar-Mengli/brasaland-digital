"""Lazy SQLModel engine and Lane-1 ensure_schema for reporting tables."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine: Engine | None = None
_schema_ready = False


def get_engine() -> Engine:
    """Create the engine on first use so importing this module needs no DATABASE_URL."""
    global _engine
    if _engine is not None:
        return _engine

    load_dotenv(Path(__file__).resolve().parent / ".env")
    database_url = os.getenv("REPORTING_DATABASE_URL") or os.getenv("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("REPORTING_DATABASE_URL or DATABASE_URL is not set")

    _engine = create_engine(database_url, echo=False, pool_pre_ping=True)

    if _engine.dialect.name == "sqlite":

        @event.listens_for(_engine, "connect")
        def _sqlite_enable_foreign_keys(
            dbapi_connection: object, connection_record: object
        ) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def _ensure_pipelines_importable() -> None:
    """Put repo ``data/`` on sys.path (same rule as config.py; no ``import config``)."""
    data_root = str((Path(__file__).resolve().parents[2] / "data").resolve())
    if data_root not in sys.path:
        sys.path.insert(0, data_root)


def ensure_schema() -> None:
    """Create reporting.* tables from data/pipelines/db_models (SQLite tests only)."""
    global _schema_ready

    if _schema_ready:
        return

    engine = get_engine()
    if engine.dialect.name == "postgresql":
        _schema_ready = True
        return

    _ensure_pipelines_importable()
    import pipelines.db_models  # noqa: F401 — register SQLModel tables on metadata

    SQLModel.metadata.create_all(engine)
    _schema_ready = True


_dead_letters_ready = False


def ensure_task_dead_letters_schema() -> None:
    """Create reporting.task_dead_letters only (SQLite tests)."""
    global _dead_letters_ready

    if _dead_letters_ready:
        return

    engine = get_engine()
    if engine.dialect.name == "postgresql":
        _dead_letters_ready = True
        return

    _ensure_pipelines_importable()
    from pipelines.db_models import TaskDeadLetter

    SQLModel.metadata.create_all(engine, tables=[TaskDeadLetter.__table__])
    _dead_letters_ready = True


def get_session() -> Session:
    return Session(get_engine())
