from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from app import app
from request_log import ACCESS_LOGGER_NAME


def test_livez_sets_request_id_and_is_not_access_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER_NAME)
    with TestClient(app) as client:
        response = client.get("/livez")
    assert response.status_code == 200
    assert response.headers.get("x-request-id")
    assert caplog.records == []


def test_honors_incoming_request_id_and_logs_allowlist(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER_NAME)
    with TestClient(app) as client:
        response = client.get("/", headers={"X-Request-ID": "smoke-req-1"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "smoke-req-1"
    assert len(caplog.records) == 1
    payload = json.loads(caplog.records[0].getMessage())
    assert payload["method"] == "GET"
    assert payload["path"] == "/"
    assert payload["status"] == 200
    assert payload["request_id"] == "smoke-req-1"
    assert "duration_ms" in payload
    assert set(payload) == {
        "method",
        "path",
        "status",
        "duration_ms",
        "request_id",
    }
