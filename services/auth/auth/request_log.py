"""Request-ID + allowlisted access log. The single access-log source for auth.

Disables uvicorn's default access logger so these JSON lines are not duplicated.
``/livez`` and ``/readyz`` are excluded (Compose healthchecks every ~30s).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

ACCESS_LOGGER_NAME = "brasaland.access"
_SKIP_PATHS = frozenset({"/livez", "/readyz"})
_REQUEST_ID_HEADER = "x-request-id"

logger = logging.getLogger(ACCESS_LOGGER_NAME)


def disable_uvicorn_access_log() -> None:
    """Make this middleware the only HTTP access-log source."""
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = True
    uvicorn_access.propagate = False


class RequestIdAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(_REQUEST_ID_HEADER, "").strip()
        request_id = incoming or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        if request.url.path not in _SKIP_PATHS:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.info(
                json.dumps(
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                        "duration_ms": duration_ms,
                        "request_id": request_id,
                    },
                    separators=(",", ":"),
                )
            )
        return response
