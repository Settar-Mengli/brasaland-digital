from __future__ import annotations

import logging

from fastapi import FastAPI

import config  # noqa: F401 — loads TELEMETRY_ENDPOINT from environment
from routers.telemetry import router as telemetry_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Brasaland Telemetry API")
app.include_router(telemetry_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "telemetry"}
