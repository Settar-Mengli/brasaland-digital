from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from brasaland_auth_verify.verify import ensure_jwt_configured
from fastapi import FastAPI

import config  # noqa: F401 — loads TELEMETRY_ENDPOINT from environment
from routers.telemetry import router as telemetry_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_jwt_configured()
    yield


app = FastAPI(title="Brasaland Telemetry API", lifespan=lifespan)
app.include_router(telemetry_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "telemetry"}
