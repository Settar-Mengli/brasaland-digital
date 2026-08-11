from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

import config  # noqa: F401 — sys.path for data/pipelines + root .env
from database import ensure_schema
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
    yield


app = FastAPI(title="Brasaland RFP API", lifespan=lifespan)
app.include_router(rfp_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "rfp", "status": "ok"}
