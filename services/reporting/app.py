from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

import config  # noqa: F401 — sys.path for data/pipelines + .env
from routers.reporting import router as reporting_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create reporting tables when DATABASE_URL is set; skip patiently when unset."""
    try:
        from database import ensure_schema

        ensure_schema()
    except RuntimeError as exc:
        logger.warning("ensure_schema skipped at startup: %s", exc)
    yield


app = FastAPI(title="Brasaland Reporting API", lifespan=lifespan)
app.include_router(reporting_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "reporting"}
