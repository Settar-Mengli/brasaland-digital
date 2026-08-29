from __future__ import annotations

import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app as app_module
from tests.helpers import assign_test_location, login_form


@pytest.fixture
def client() -> TestClient:
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture
def capture_reset_email(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []

    def fake_send(to_email: str, token: str) -> None:
        calls.append({"to_email": to_email, "token": token})

    monkeypatch.setattr(app_module, "send_password_reset_email", fake_send)
    return calls


def test_forgot_password_registered_email_sends_and_returns_generic_message(
    client: TestClient,
    capture_reset_email: list[dict[str, str]],
) -> None:
    client.post(
        "/auth/register",
        json={"email": "forgot-known@brasaland.com", "password": "password123"},
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": "forgot-known@brasaland.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": app_module.FORGOT_PASSWORD_MESSAGE,
    }
    assert len(capture_reset_email) == 1
    assert capture_reset_email[0]["to_email"] == "forgot-known@brasaland.com"
    assert capture_reset_email[0]["token"]


def test_forgot_password_unknown_email_matches_registered_response(
    client: TestClient,
    capture_reset_email: list[dict[str, str]],
) -> None:
    client.post(
        "/auth/register",
        json={"email": "forgot-known2@brasaland.com", "password": "password123"},
    )

    known_response = client.post(
        "/auth/forgot-password",
        json={"email": "forgot-known2@brasaland.com"},
    )
    unknown_response = client.post(
        "/auth/forgot-password",
        json={"email": "forgot-missing@brasaland.com"},
    )

    assert known_response.status_code == 200
    assert unknown_response.status_code == 200
    assert known_response.json() == unknown_response.json()
    assert known_response.json() == {
        "message": app_module.FORGOT_PASSWORD_MESSAGE,
    }
    assert len(capture_reset_email) == 1


def test_forgot_password_send_failure_still_returns_generic_message(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def failing_send(to_email: str, token: str) -> None:
        raise RuntimeError("Resend API unavailable")

    monkeypatch.setattr(app_module, "send_password_reset_email", failing_send)
    caplog.set_level(logging.ERROR)

    client.post(
        "/auth/register",
        json={"email": "forgot-sendfail@brasaland.com", "password": "password123"},
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": "forgot-sendfail@brasaland.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": app_module.FORGOT_PASSWORD_MESSAGE,
    }
    log_text = caplog.text
    assert "password_reset_email_failed" in log_text
    assert "token=" not in log_text
    assert "/reset-password?" not in log_text
    assert "Traceback" not in log_text
    assert "Resend API unavailable" not in log_text


def test_forgot_password_reset_login_full_flow(
    client: TestClient,
    capture_reset_email: list[dict[str, str]],
) -> None:
    email = "forgot-flow@brasaland.com"
    old_password = "password123"
    new_password = "newpassword1"

    client.post(
        "/auth/register",
        json={"email": email, "password": old_password},
    )
    assign_test_location(email)

    forgot = client.post("/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    assert len(capture_reset_email) == 1
    reset_token = capture_reset_email[0]["token"]

    reset = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    )
    assert reset.status_code == 200
    assert reset.json()["message"] == "Password has been reset. You can now log in."

    new_login = client.post(
        "/auth/login",
        data=login_form(email, new_password),
    )
    assert new_login.status_code == 200

    old_login = client.post(
        "/auth/login",
        data=login_form(email, old_password),
    )
    assert old_login.status_code == 401


def test_reset_password_invalid_token_returns_400(client: TestClient) -> None:
    response = client.post(
        "/auth/reset-password",
        json={"token": "not-a-valid-reset-token", "new_password": "newpassword1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


def test_reset_password_reused_token_returns_400(
    client: TestClient,
    capture_reset_email: list[dict[str, str]],
) -> None:
    email = "forgot-reuse@brasaland.com"
    client.post(
        "/auth/register",
        json={"email": email, "password": "password123"},
    )
    client.post("/auth/forgot-password", json={"email": email})
    reset_token = capture_reset_email[0]["token"]

    first = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword1"},
    )
    assert first.status_code == 200

    second = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "anotherpass1"},
    )
    assert second.status_code == 400
    assert second.json()["detail"] == "Invalid or expired reset token"
