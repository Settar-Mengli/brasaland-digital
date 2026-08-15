import logging
import time
from datetime import UTC, datetime

from typing import Annotated

from brasaland_auth_verify.deps import get_current_user_uuid, get_optional_user_uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import ValidationError

from allowlists import validate_event_properties
from models import EventsIngestBody, IngestResponse, TelemetryEvent
from rate_limit import INGEST_RATE_LIMIT, limiter
from report_service import get_report_payload
from repository import bulk_insert_events
from row_builder import build_event_row

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry")

MAX_EVENTS_PER_REQUEST = 50
ANONYMOUS_USER_ID = "anonymous"


@router.get("/report")
def get_report(
    _user: Annotated[str, Depends(get_current_user_uuid)],
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> dict[str, object]:
    return get_report_payload(
        start_date,
        end_date,
        now_fn=lambda: datetime.now(UTC),
        monotonic_fn=time.monotonic,
    )


@router.post("/events", response_model=IngestResponse)
@limiter.limit(INGEST_RATE_LIMIT)
def ingest_events(
    request: Request,
    body: Annotated[EventsIngestBody, Body()],
    user_uuid: Annotated[str | None, Depends(get_optional_user_uuid)],
) -> IngestResponse:
    if len(body.events) > MAX_EVENTS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"At most {MAX_EVENTS_PER_REQUEST} events per request",
        )

    received = len(body.events)
    pending_rows: list[dict[str, object]] = []
    resolved_user_id = user_uuid if user_uuid is not None else ANONYMOUS_USER_ID

    for index, raw_event in enumerate(body.events):
        try:
            event = TelemetryEvent.model_validate(raw_event).model_copy(
                update={"userId": resolved_user_id}
            )
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
