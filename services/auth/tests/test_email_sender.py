from __future__ import annotations

from typing import Any

import pytest

import auth.email_sender as email_sender_module
from auth.email_sender import send_password_reset_email


@pytest.fixture
def resend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESET_EMAIL_FROM", "onboarding@resend.dev")
    monkeypatch.setenv(
        "RESET_LINK_BASE_URL",
        "http://127.0.0.1:8002",
    )


def test_send_password_reset_email_builds_link_and_payload(
    monkeypatch: pytest.MonkeyPatch,
    resend_env: None,
) -> None:
    captured: dict[str, Any] = {}

    def fake_send(params: dict[str, Any]) -> dict[str, str]:
        captured["params"] = params
        captured["api_key"] = email_sender_module.resend.api_key
        return {"id": "email_123"}

    monkeypatch.setattr(email_sender_module.resend.Emails, "send", fake_send)

    token = "sample-reset-token-value"
    send_password_reset_email("user@brasaland.com", token)

    params = captured["params"]
    expected_link = (
        f"http://127.0.0.1:8002/reset-password?token={token}"
    )

    assert captured["api_key"] == "re_test_key"
    assert params["from"] == "onboarding@resend.dev"
    assert params["to"] == ["user@brasaland.com"]
    assert params["subject"] == "Reset your Brasaland password"
    assert expected_link in params["text"]
    assert expected_link in params["html"]


def test_send_password_reset_email_missing_api_key_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("RESET_EMAIL_FROM", "onboarding@resend.dev")
    monkeypatch.setenv("RESET_LINK_BASE_URL", "http://127.0.0.1:8002")

    def fake_send(params: dict[str, Any]) -> dict[str, str]:
        raise AssertionError("resend.Emails.send must not be called")

    monkeypatch.setattr(email_sender_module.resend.Emails, "send", fake_send)

    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        send_password_reset_email("user@brasaland.com", "unused-token")
