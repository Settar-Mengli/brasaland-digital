from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

import app as app_module
from auth.request_log import ACCESS_LOGGER_NAME
from tests.helpers import login_form


def test_livez_sets_request_id_and_is_not_access_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER_NAME)
    with TestClient(app_module.app) as client:
        response = client.get("/livez")
    assert response.status_code == 200
    assert response.headers.get("x-request-id")
    assert caplog.records == []


def test_honors_incoming_request_id_and_logs_allowlist(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER_NAME)
    with TestClient(app_module.app) as client:
        response = client.get("/", headers={"X-Request-ID": "smoke-req-1"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "smoke-req-1"
    assert len(caplog.records) == 1
    payload = json.loads(caplog.records[0].getMessage())
    assert payload == {
        "method": "GET",
        "path": "/",
        "status": 200,
        "duration_ms": payload["duration_ms"],
        "request_id": "smoke-req-1",
    }
    assert set(payload) == {
        "method",
        "path",
        "status",
        "duration_ms",
        "request_id",
    }


def test_login_access_log_does_not_include_password(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=ACCESS_LOGGER_NAME)
    secret = "password-must-not-appear-in-logs"
    with TestClient(app_module.app) as client:
        client.post(
            "/auth/login",
            data=login_form("nobody@brasaland.com", secret),
        )
    text = caplog.text
    assert secret not in text
    assert "Authorization" not in text
    assert "DATABASE_URL" not in text
