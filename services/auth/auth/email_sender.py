from __future__ import annotations

import os
from pathlib import Path

import resend
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

_RESET_SUBJECT = "Reset your Brasaland password"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def send_password_reset_email(to_email: str, token: str) -> None:
    api_key = _require_env("RESEND_API_KEY")
    from_address = _require_env("RESET_EMAIL_FROM")
    link_base = _require_env("RESET_LINK_BASE_URL")
    reset_link = f"{link_base}/reset-password?token={token}"

    text_body = (
        "You requested a password reset for your Brasaland account.\n\n"
        f"Reset your password using this link:\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html_body = (
        "<p>You requested a password reset for your Brasaland account.</p>"
        f'<p><a href="{reset_link}">Reset your password</a></p>'
        f"<p>Or copy this link into your browser:<br>{reset_link}</p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )

    resend.api_key = api_key
    resend.Emails.send(
        {
            "from": from_address,
            "to": [to_email],
            "subject": _RESET_SUBJECT,
            "text": text_body,
            "html": html_body,
        }
    )
