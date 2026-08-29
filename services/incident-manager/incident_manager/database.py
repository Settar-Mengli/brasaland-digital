from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("INCIDENT_DATABASE_URL") or os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("INCIDENT_DATABASE_URL or DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

_schema_ready = False

if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def _sqlite_enable_foreign_keys(
        dbapi_connection: object, connection_record: object
    ) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def ensure_schema() -> None:
    global _schema_ready

    if _schema_ready:
        return

    if engine.dialect.name == "postgresql":
        _schema_ready = True
        return

    import incident_manager.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _schema_ready = True


def get_session() -> Session:
    return Session(engine)
