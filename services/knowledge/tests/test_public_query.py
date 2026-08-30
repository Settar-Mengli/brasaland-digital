"""API tests for POST /public/knowledge/query."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app import app
from brasaland_auth_verify.testing import mint_access_token
from fastapi.testclient import TestClient
from tests.conftest import PRIVATE_PEM

PUBLIC_PATH = "/public/knowledge/query"
SVC_CLAIM = "website-knowledge"
REFUSAL_ANSWER = (
    "I don't have verified public information for that yet. "
    "Please ask a team member or check our website."
)


def _website_bearer(**mint_kwargs: object) -> dict[str, str]:
    token = mint_access_token(
        PRIVATE_PEM,
        extra_claims={"svc": SVC_CLAIM},
        **mint_kwargs,  # type: ignore[arg-type]
    )
    return {"Authorization": f"Bearer {token}"}


def _human_bearer() -> dict[str, str]:
    token = mint_access_token(PRIVATE_PEM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def enabled_public_knowledge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_KNOWLEDGE_ENABLED", "true")


def test_public_query_unauthorized() -> None:
    client = TestClient(app)
    response = client.post(PUBLIC_PATH, json={"question": "What are your hours?"})
    assert response.status_code == 401


def test_public_query_human_jwt_forbidden(enabled_public_knowledge: None) -> None:
    client = TestClient(app)
    response = client.post(
        PUBLIC_PATH,
        headers=_human_bearer(),
        json={"question": "What are your hours?"},
    )
    assert response.status_code == 403


def test_public_query_disabled_returns_503() -> None:
    client = TestClient(app)
    response = client.post(
        PUBLIC_PATH,
        headers=_website_bearer(),
        json={"question": "What are your hours?"},
    )
    assert response.status_code == 503


def test_public_query_success_with_mocked_public_rag(
    enabled_public_knowledge: None,
) -> None:
    client = TestClient(app)
    with patch(
        "pipelines.public_rag.query_public",
        return_value="We are open 11am–10pm daily.",
    ) as query_mock:
        response = client.post(
            PUBLIC_PATH,
            headers=_website_bearer(),
            json={"question": "What are your hours?"},
        )

    assert response.status_code == 200
    assert response.json() == {"answer": "We are open 11am–10pm daily."}
    assert set(response.json().keys()) == {"answer"}
    query_mock.assert_called_once_with("What are your hours?")


def test_public_query_empty_question_returns_422(
    enabled_public_knowledge: None,
) -> None:
    client = TestClient(app)
    response = client.post(
        PUBLIC_PATH,
        headers=_website_bearer(),
        json={"question": "   "},
    )
    assert response.status_code == 422


def test_public_query_too_long_question_returns_422(
    enabled_public_knowledge: None,
) -> None:
    client = TestClient(app)
    response = client.post(
        PUBLIC_PATH,
        headers=_website_bearer(),
        json={"question": "x" * 301},
    )
    assert response.status_code == 422


def test_public_query_not_indexed_returns_503(
    enabled_public_knowledge: None,
) -> None:
    from pipelines.rag import PublicKnowledgeNotIndexedError

    client = TestClient(app)
    with patch(
        "pipelines.public_rag.query_public",
        side_effect=PublicKnowledgeNotIndexedError("missing"),
    ):
        response = client.post(
            PUBLIC_PATH,
            headers=_website_bearer(),
            json={"question": "What are your hours?"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Public knowledge is not available"


def test_public_query_internal_question_refusal_no_leak(
    enabled_public_knowledge: None,
) -> None:
    client = TestClient(app)
    with patch(
        "pipelines.public_rag.query_public",
        return_value=REFUSAL_ANSWER,
    ):
        response = client.post(
            PUBLIC_PATH,
            headers=_website_bearer(),
            json={"question": "What is the secret prep recipe ratio?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body == {"answer": REFUSAL_ANSWER}
    assert "recipe" not in body["answer"].lower() or "verified public" in body["answer"]


def test_public_query_rate_limit_returns_429(
    enabled_public_knowledge: None,
) -> None:
    limiter = app.state.limiter
    was = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    try:
        client = TestClient(app)
        with patch(
            "pipelines.public_rag.query_public",
            return_value="ok",
        ):
            codes = [
                client.post(
                    PUBLIC_PATH,
                    headers=_website_bearer(),
                    json={"question": "What are your hours?"},
                ).status_code
                for _ in range(8)
            ]
        assert 200 in codes
        assert 429 in codes
    finally:
        limiter.enabled = was
        limiter.reset()
