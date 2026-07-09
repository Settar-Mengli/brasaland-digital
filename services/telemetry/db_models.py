from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def _json_column() -> Column:
    return Column(JSON().with_variant(JSONB(), "postgresql"))


class TelemetryEventRow(SQLModel, table=True):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("ix_telemetry_events_timestamp", "timestamp"),
        Index("ix_telemetry_events_event_type", "event_type"),
    )

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(unique=True, index=True)
    event_type: str
    timestamp: datetime
    service: str
    level: str
    tags: dict[str, object] = Field(sa_column=_json_column())
    context: dict[str, object] = Field(sa_column=_json_column(), default_factory=dict)
