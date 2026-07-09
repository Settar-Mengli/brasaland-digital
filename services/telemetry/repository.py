from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database import ensure_schema, engine, get_session
from db_models import TelemetryEventRow


def bulk_insert_events(rows: list[dict[str, Any]]) -> int:
    ensure_schema()
    if not rows:
        return 0

    with get_session() as session:
        if engine.dialect.name == "postgresql":
            statement = pg_insert(TelemetryEventRow).values(rows)
        else:
            statement = sqlite_insert(TelemetryEventRow).values(rows)

        statement = statement.on_conflict_do_nothing(index_elements=["event_id"])
        result = session.execute(statement)
        session.commit()
        return result.rowcount or 0
