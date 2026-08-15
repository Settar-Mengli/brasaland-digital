from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from brasaland_auth_verify.deps import get_current_user_uuid
from brasaland_auth_verify.verify import ensure_jwt_configured
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from incident_manager.service import (
    build_summary,
    create_incident,
    get_incident,
    list_incidents,
    update_incident_status,
    validate_list_filters,
)
from incident_manager.types import IncidentRecord

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_jwt_configured()
    yield


app = FastAPI(title="Brasaland Incident Manager", lifespan=lifespan)


class IncidentCreate(BaseModel):
    title: str
    description: str
    category: str
    origin: str
    branch: str
    status: str = "open"


class IncidentStatusUpdate(BaseModel):
    status: str


class FieldErrorResponse(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    errors: list[FieldErrorResponse]


class IncidentResponse(BaseModel):
    id: int
    source_incident_id: str
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class IncidentSummaryResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_origin: dict[str, int]
    by_branch: dict[str, int]


def _to_response(record: IncidentRecord) -> IncidentResponse:
    return IncidentResponse(
        id=record["id"],
        source_incident_id=record["source_incident_id"],
        title=record["title"],
        description=record["description"],
        category=record["category"],
        status=record["status"],
        origin=record["origin"],
        branch=record["branch"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def _validation_http_exception(errors: list[dict[str, str]]) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "errors": [
                {"field": error["field"], "message": error["message"]} for error in errors
            ]
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
def create_incident_route(
    body: IncidentCreate,
    _user: Annotated[str, Depends(get_current_user_uuid)],
) -> IncidentResponse:
    record, field_errors = create_incident(
        {
            "title": body.title,
            "description": body.description,
            "category": body.category,
            "status": body.status,
            "origin": body.origin,
            "branch": body.branch,
        }
    )
    if field_errors:
        raise _validation_http_exception(field_errors)
    if record is None:
        raise HTTPException(status_code=400, detail={"errors": []})
    return _to_response(record)


@app.get("/api/incidents", response_model=list[IncidentResponse])
def list_incidents_route(
    status: str | None = Query(default=None),
    origin: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[IncidentResponse]:
    filter_errors = validate_list_filters(
        status=status,
        origin=origin,
        branch=branch,
        category=category,
    )
    if filter_errors:
        raise _validation_http_exception(filter_errors)

    records = list_incidents(
        status=status,
        origin=origin,
        branch=branch,
        category=category,
    )
    return [_to_response(record) for record in records]


@app.get("/api/incidents/summary", response_model=IncidentSummaryResponse)
def incident_summary_route() -> IncidentSummaryResponse:
    summary = build_summary()
    return IncidentSummaryResponse(**summary)


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident_route(incident_id: int) -> IncidentResponse:
    record = get_incident(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _to_response(record)


@app.patch("/api/incidents/{incident_id}/status", response_model=IncidentResponse)
def patch_incident_status_route(
    incident_id: int,
    body: IncidentStatusUpdate,
    _user: Annotated[str, Depends(get_current_user_uuid)],
) -> IncidentResponse:
    record, transition_message = update_incident_status(incident_id, body.status)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if transition_message is not None:
        raise HTTPException(status_code=400, detail=transition_message)
    return _to_response(record)


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
