from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import ValidationError

from allowlists import validate_event_properties
from models import EventsIngestBody, IngestResponse, TelemetryEvent
from repository import bulk_insert_events
from row_builder import build_event_row

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry")


@router.post("/events", response_model=IngestResponse)
def ingest_events(body: EventsIngestBody) -> IngestResponse:
    received = len(body.events)
    pending_rows: list[dict[str, object]] = []

    for index, raw_event in enumerate(body.events):
        try:
            event = TelemetryEvent.model_validate(raw_event)
        except ValidationError as error:
            logger.warning(
                "Rejected telemetry event at index %d (envelope): %s",
                index,
                error.errors()[0]["msg"] if error.errors() else str(error),
            )
            continue

        allowlist_error = validate_event_properties(event.event_type, event.properties)
        if allowlist_error is not None:
            logger.warning(
                "Rejected telemetry event at index %d (allowlist): %s",
                index,
                allowlist_error,
            )
            continue

        pending_rows.append(build_event_row(event))

    stored = bulk_insert_events(pending_rows)
    rejected = received - stored

    logger.info(
        "Telemetry ingest received=%d stored=%d rejected=%d",
        received,
        stored,
        rejected,
    )
    return IngestResponse(received=received, stored=stored, rejected=rejected)
