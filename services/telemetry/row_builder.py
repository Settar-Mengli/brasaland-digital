from __future__ import annotations

from datetime import datetime
from typing import Any

from level import derive_level
from models import TelemetryEvent


def build_event_row(event: TelemetryEvent) -> dict[str, Any]:
    return {
        "event_id": event.eventId,
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "service": event.service,
        "level": derive_level(event.event_type),
        "tags": event.properties,
        "context": {
            "sessionId": event.sessionId,
            "userId": event.userId,
            "requestId": event.requestId,
            "schemaVersion": event.schemaVersion,
        },
    }


def rows_from_events(events: list[TelemetryEvent]) -> list[dict[str, Any]]:
    return [build_event_row(event) for event in events]
