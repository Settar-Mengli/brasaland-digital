from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Incident(SQLModel, table=True):
    __tablename__ = "incident"

    id: int | None = Field(default=None, primary_key=True)
    source_incident_id: str = Field(unique=True)
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
