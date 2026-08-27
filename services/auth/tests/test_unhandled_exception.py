from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import app as app_module

_TEST_BOOM_PATH = "/__test__/boom"


@pytest.fixture
def boom_route() -> Generator[None, None, None]:
    def _boom() -> None:
        raise RuntimeError("test boom")

    route = APIRoute(_TEST_BOOM_PATH, endpoint=_boom, methods=["GET"])
    app_module.app.router.routes.append(route)
    try:
        yield
    finally:
        app_module.app.router.routes.remove(route)


def test_unhandled_500_logs_path_not_query(
    boom_route: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        response = client.get(
            f"{_TEST_BOOM_PATH}?token=secret-leak&x=1",
            headers={"X-Request-ID": "test-req-500"},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}

    log_text = caplog.text
    assert "token=secret-leak" not in log_text
    assert "Traceback" not in log_text

    uvicorn_error_records = [
        record for record in caplog.records if record.name == "uvicorn.error"
    ]
    assert all("token=secret-leak" not in record.getMessage() for record in uvicorn_error_records)

    app_error_records = [
        record
        for record in caplog.records
        if record.name == "app" and record.getMessage() == "unhandled_server_error"
    ]
    assert len(app_error_records) == 1
    record = app_error_records[0]
    assert record.path == _TEST_BOOM_PATH
    assert record.request_id == "test-req-500"
