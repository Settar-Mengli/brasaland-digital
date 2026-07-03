from __future__ import annotations

import os
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

os.environ["DATABASE_URL"] = "sqlite://"

import incident_manager.database as database
import incident_manager.models  # noqa: F401
from incident_manager.models import Incident


_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


database.engine = _test_engine
database._schema_ready = False


def test_incident_model_imports_and_ensure_schema_creates_table() -> None:
    database.ensure_schema()

    table_names = inspect(_test_engine).get_table_names()
    assert "incident" in table_names

    incident_columns = {column["name"] for column in inspect(_test_engine).get_columns("incident")}
    assert incident_columns == {
        "id",
        "source_incident_id",
        "title",
        "description",
        "category",
        "status",
        "origin",
        "branch",
        "created_at",
        "updated_at",
    }

    assert Incident.__tablename__ == "incident"

    SQLModel.metadata.drop_all(_test_engine)
