from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    eventId: str
    timestamp: datetime
    sessionId: str
    userId: str
    event_type: str
    schemaVersion: str
    requestId: str
    service: str
    properties: dict[str, Any] = Field(default_factory=dict)


class EventsIngestBody(BaseModel):
    events: list[dict[str, Any]]


class IngestResponse(BaseModel):
    received: int
    stored: int
    rejected: int
