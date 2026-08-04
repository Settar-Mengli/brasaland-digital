from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import event
from sqlmodel import Session, create_engine

load_dotenv(Path(__file__).parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def _sqlite_enable_foreign_keys(
        dbapi_connection: object, connection_record: object
    ) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
