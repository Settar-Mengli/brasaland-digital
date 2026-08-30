"""Unit tests for public RAG profile, loaders, and facade."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelines.public_loaders import build_public_chunks, load_manifest
from pipelines.public_rag import (
    PUBLIC_NO_CONTEXT_ANSWER,
    PUBLIC_SYSTEM_PROMPT,
    build_public_user_prompt,
    generate_public_answer,
    query_public,
)
from pipelines.rag import PublicKnowledgeNotIndexedError, retrieve, setup
from pipelines.rag_profiles import PUBLIC_NO_CONTEXT_ANSWER as PROFILE_ANSWER

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ROOT = REPO_ROOT / "docs" / "public-knowledge-base"


def test_manifest_has_eight_allowlisted_sources() -> None:
    sources = load_manifest(PUBLIC_ROOT)
    assert len(sources) == 8
    paths = {s.path for s in sources}
    assert "locations.json" in paths
    assert "menu.json" in paths
    assert "loyalty.md" in paths
    assert not any("company-knowledge-base" in p for p in paths)


def test_build_public_chunks_json_and_markdown_counts() -> None:
    chunks, per_doc = build_public_chunks(PUBLIC_ROOT)
    assert per_doc["locations.json"] == 14
    assert per_doc["menu.json"] == 10
    assert per_doc["loyalty.md"] >= 3
    assert len(chunks) >= 24 + 18

    for chunk in chunks:
        assert chunk["audience"] == "public"
        assert chunk.get("topic")
        assert chunk.get("record_id")
        assert chunk.get("locale") == "en"
        assert chunk.get("last_verified_at")


def test_build_public_chunks_never_reads_staff_corpus() -> None:
    with patch(
        "pipelines.public_loaders.chunk_markdown",
        side_effect=lambda text, source_document: [
            {
                "company": "brasaland",
                "source_document": source_document,
                "section": "s",
                "language": "en",
                "chunk_index": 0,
                "text": "x",
            }
        ],
    ):
        chunks, _ = build_public_chunks(PUBLIC_ROOT)
    for chunk in chunks:
        assert "waste-protocol" not in chunk.get("source_document", "")
        assert "supplier-ordering" not in chunk.get("source_document", "")


def test_public_setup_deletes_only_public_collection(tmp_path: Path) -> None:
    import shutil

    shutil.copytree(PUBLIC_ROOT, tmp_path / "corpus")
    client = MagicMock()
    client.collection_exists.return_value = True

    with (
        patch("pipelines.rag.get_qdrant_client", return_value=client),
        patch("pipelines.rag.embed", return_value=[0.0] * 384),
    ):
        summary = setup(corpus_path=tmp_path / "corpus", profile="public")

    client.delete_collection.assert_called_once_with("brasaland_knowledge_public")
    assert summary["collection"] == "brasaland_knowledge_public"
    assert summary["points"] >= 24


def test_public_setup_preflight_skips_delete_on_missing_source(tmp_path: Path) -> None:
    import shutil

    shutil.copytree(PUBLIC_ROOT, tmp_path / "corpus")
    (tmp_path / "corpus" / "contact.md").unlink()
    client = MagicMock()

    with (
        patch("pipelines.rag.get_qdrant_client", return_value=client),
        patch("pipelines.rag.embed", return_value=[0.0] * 384),
        pytest.raises(FileNotFoundError),
    ):
        setup(corpus_path=tmp_path / "corpus", profile="public")

    client.delete_collection.assert_not_called()


def test_public_retrieve_missing_collection_raises_no_staff_fallback() -> None:
    client = MagicMock()
    client.collection_exists.return_value = False

    with (
        patch("pipelines.rag.embed", return_value=[0.1] * 384),
        patch("pipelines.rag.get_qdrant_client", return_value=client),
        pytest.raises(PublicKnowledgeNotIndexedError),
    ):
        retrieve("hours?", profile="public")

    client.query_points.assert_not_called()


def test_public_retrieve_uses_audience_filter_and_post_filter() -> None:
    fake_hits = [
        SimpleNamespace(
            score=0.8,
            payload={
                "text": "public fact",
                "audience": "public",
                "source_document": "menu.json",
            },
        ),
        SimpleNamespace(
            score=0.9,
            payload={
                "text": "staff leak",
                "audience": "staff",
                "source_document": "loyalty-program",
            },
        ),
    ]
    client = MagicMock()
    client.collection_exists.return_value = True
    client.query_points.return_value = SimpleNamespace(points=fake_hits)

    with (
        patch("pipelines.rag.embed", return_value=[0.1] * 384),
        patch("pipelines.rag.get_qdrant_client", return_value=client),
    ):
        results = retrieve("menu price", profile="public", min_score=0.45)

    assert client.query_points.call_args.kwargs["collection_name"] == (
        "brasaland_knowledge_public"
    )
    assert "query_filter" in client.query_points.call_args.kwargs
    assert len(results) == 1
    assert results[0]["text"] == "public fact"


def test_query_public_empty_context_returns_fixed_answer_without_llm() -> None:
    with (
        patch("pipelines.public_rag.retrieve", return_value=[]),
        patch("pipelines.public_rag._bounded_chat_completion") as completion_mock,
    ):
        answer = query_public("random question")

    assert answer == PUBLIC_NO_CONTEXT_ANSWER
    assert answer == PROFILE_ANSWER
    completion_mock.assert_not_called()


def test_generate_public_answer_passes_max_tokens() -> None:
    chunks = [
        {
            "text": "Earn 1 point per 10,000 COP spent.",
            "source_document": "loyalty.md",
            "topic": "loyalty",
            "record_id": "loyalty:0",
            "section": "Earn",
        }
    ]
    with patch(
        "pipelines.public_rag._bounded_chat_completion",
        return_value="10,000 COP earns one point.",
    ) as completion_mock:
        answer = generate_public_answer("earn rate?", chunks)

    assert "10,000 COP" in answer
    kwargs = completion_mock.call_args.kwargs
    assert kwargs["max_tokens"] == 512
    assert kwargs["max_tier_attempts"] == 2
    assert kwargs["temperature"] == 0.1


def test_public_system_prompt_refuses_internal_data() -> None:
    assert "internal" in PUBLIC_SYSTEM_PROMPT.lower()
    assert "recipe" in PUBLIC_SYSTEM_PROMPT.lower()
    assert "cross-contamination" in PUBLIC_SYSTEM_PROMPT.lower()


def test_build_public_user_prompt_fences_retrieved_data() -> None:
    prompt = build_public_user_prompt(
        "price?",
        [{"text": "COP 95000", "source_document": "menu.json", "section": "Sirloin"}],
    )
    assert "<<<RETRIEVED_DATA>>>" in prompt
    assert "COP 95000" in prompt
    assert "<<<AGENT_MEMORY>>>" not in prompt


def test_menu_chunk_preserves_currency_values() -> None:
    chunks, _ = build_public_chunks(PUBLIC_ROOT)
    sirloin = next(
        c for c in chunks if c.get("record_id") == "guest-menu-sirloin"
    )
    assert "95000" in sirloin["text"]
    assert "28" in sirloin["text"]


def test_loyalty_chunk_preserves_cop_threshold() -> None:
    chunks, _ = build_public_chunks(PUBLIC_ROOT)
    loyalty_chunks = [c for c in chunks if c.get("topic") == "loyalty"]
    combined = "\n".join(c["text"] for c in loyalty_chunks)
    assert "10,000 COP" in combined or "10000" in combined.replace(",", "")
