from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import ValidationError

from models import EventsIngestBody, IngestResponse, TelemetryEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry")


@router.post("/events", response_model=IngestResponse)
def ingest_events(body: EventsIngestBody) -> IngestResponse:
    # Stub: replaced with real storage in the next phase.
    # Per-event "stored"/"rejected" counting arrives in the storage phase.
    for index, raw_event in enumerate(body.events):
        try:
            event = TelemetryEvent.model_validate(raw_event)
        except ValidationError as error:
            logger.warning(
                "Rejected telemetry event at index %d: %s",
                index,
                error.errors()[0]["msg"] if error.errors() else str(error),
            )
            continue
        logger.info("event_type=%s", event.event_type)

    logger.info("Received %d telemetry events", len(body.events))
    return IngestResponse(received=len(body.events))
