"""Celery application for the reporting service (Redis broker + result backend).

``task_acks_late=True``: the worker acks after the task finishes so a crash mid-run
redelivers the message.
"""

from __future__ import annotations

import os
from pathlib import Path

from celery import Celery
from dotenv import load_dotenv


def _resolve_redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if url:
        return url
    load_dotenv(Path(__file__).resolve().parent / ".env")
    url = os.environ.get("REDIS_URL")
    if url:
        return url
    # Import-safe default so uvicorn can start; lifespan warns when unset.
    # Enqueue/worker still need a reachable Redis at REDIS_URL.
    return "redis://127.0.0.1:6379/0"


redis_url = _resolve_redis_url()

celery_app = Celery(
    "reporting",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,
    task_track_started=True,
    task_acks_late=True,
    timezone="UTC",
    enable_utc=True,
)
