"""Lazy SQLModel engine and Lane-1 ensure_schema for reporting tables."""

from __future__ import annotations

import os
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
    database_url = os.getenv("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("DATABASE_URL is not set")

    _engine = create_engine(database_url, echo=False)

    if _engine.dialect.name == "sqlite":

        @event.listens_for(_engine, "connect")
        def _sqlite_enable_foreign_keys(
            dbapi_connection: object, connection_record: object
        ) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def ensure_schema() -> None:
    """Create reporting.* tables from data/pipelines/db_models (Lane-1 source of truth)."""
    global _schema_ready

    if _schema_ready:
        return

    import config  # noqa: F401 — ensures data/ is on sys.path
    import pipelines.db_models  # noqa: F401 — register SQLModel tables on metadata

    SQLModel.metadata.create_all(get_engine())
    _schema_ready = True


def get_session() -> Session:
    return Session(get_engine())
