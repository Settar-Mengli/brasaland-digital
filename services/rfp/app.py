from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.requests import Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from brasaland_auth_verify.surface import fastapi_docs_kwargs

import config  # noqa: F401 — sys.path for data/pipelines + root .env
from checkpointer import run_setup
from database import ensure_schema
from health import rfp_ready_reason
from rate_limit import limiter
from request_log import RequestIdAccessLogMiddleware, disable_uvicorn_access_log
from routers.rfp import router as rfp_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if not os.environ.get("REDIS_URL"):
        logger.warning(
            "REDIS_URL is not set; POST /rfp/tickets enqueue requires Redis "
            "(Celery broker/backend)"
        )
    ensure_schema()
    run_setup()
    yield


app = FastAPI(
    title="Brasaland RFP API",
    lifespan=lifespan,
    **fastapi_docs_kwargs(),
)
disable_uvicorn_access_log()
app.add_middleware(RequestIdAccessLogMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unhandled_server_error",
        extra={"path": request.url.path, "request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


app.include_router(rfp_router)


@app.get("/livez")
def livez() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    reason = rfp_ready_reason()
    if reason is None:
        return JSONResponse({"status": "ok"})
    return JSONResponse(
        {"status": "unavailable", "reason": reason},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "rfp", "status": "ok"}
