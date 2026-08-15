"""RFP test fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest


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
