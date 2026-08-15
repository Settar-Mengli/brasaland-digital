from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from brasaland_auth_verify.verify import ensure_jwt_configured
from fastapi import FastAPI

import config  # noqa: F401 — sys.path for data/pipelines + .env
from routers.reporting import router as reporting_router
from routers.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create reporting tables when DATABASE_URL is set; skip patiently when unset."""
    ensure_jwt_configured()
    if not os.environ.get("REDIS_URL"):
        logger.warning(
            "REDIS_URL is not set; POST /reporting/pipeline-runs and GET /tasks "
            "require Redis (Celery broker/backend)"
        )
    try:
        from database import ensure_schema, ensure_task_dead_letters_schema

        ensure_schema()
        ensure_task_dead_letters_schema()
    except RuntimeError as exc:
        logger.warning("ensure_schema skipped at startup: %s", exc)
    yield


app = FastAPI(title="Brasaland Reporting API", lifespan=lifespan)
app.include_router(reporting_router)
app.include_router(tasks_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "reporting"}
