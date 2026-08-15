"""FastAPI surface helpers (docs gating). No rate-limit deps here."""

from __future__ import annotations

import os
from typing import Any


def docs_exposed() -> bool:
    """True when OpenAPI/Swagger should be published."""
    return os.environ.get("EXPOSE_DOCS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def fastapi_docs_kwargs() -> dict[str, Any]:
    """Pass into ``FastAPI(**fastapi_docs_kwargs())``.

    When ``EXPOSE_DOCS`` is unset/false, docs, ReDoc, and openapi.json are disabled.
    """
    if docs_exposed():
        return {}
    return {"docs_url": None, "redoc_url": None, "openapi_url": None}
