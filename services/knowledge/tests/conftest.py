"""Knowledge service test bootstrap."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest

# Avoid JWT env requirement during import of dependencies in some paths.
os.environ.setdefault("JWT_ALGORITHM", "RS256")

import config  # noqa: E402, F401 — data/ on sys.path


@pytest.fixture(autouse=True)
def disable_rate_limits() -> Generator[None, None, None]:
    from app import app

    limiter = getattr(app.state, "limiter", None)
    if limiter is None:
        yield
        return
    was = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was
