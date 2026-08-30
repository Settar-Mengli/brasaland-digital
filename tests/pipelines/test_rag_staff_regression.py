"""Staff RAG regression guards — byte-compatible defaults and import isolation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pipelines.rag import (
    COLLECTION_NAME,
    DEFAULT_MIN_SCORE,
    SOURCE_DOCUMENTS,
    SYSTEM_PROMPT,
    query,
    retrieve,
    setup,
)
from pipelines.rag_profiles import STAFF_PROFILE, STAFF_SOURCE_STEMS

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "docs" / "company-knowledge-base"

SYSTEM_PROMPT_SHA256 = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()


def test_collection_name_staff_alias() -> None:
    assert COLLECTION_NAME == "brasaland_knowledge"
    assert COLLECTION_NAME == STAFF_PROFILE.collection_name


def test_source_documents_tuple_unchanged() -> None:
    assert SOURCE_DOCUMENTS == STAFF_SOURCE_STEMS
    assert SOURCE_DOCUMENTS == (
        "loyalty-program",
        "waste-protocol",
        "menu-allergens",
        "supplier-ordering",
    )


def test_system_prompt_snapshot_guard() -> None:
    assert hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == (
        SYSTEM_PROMPT_SHA256
    )


def test_retrieve_default_uses_staff_collection_and_min_score() -> None:
    client = MagicMock()
    client.query_points.return_value = MagicMock(points=[])

    with (
        patch("pipelines.rag.embed", return_value=[0.1] * 384),
        patch("pipelines.rag.get_qdrant_client", return_value=client),
    ):
        retrieve("hours?")

    client.query_points.assert_called_once()
    kwargs = client.query_points.call_args.kwargs
    assert kwargs["collection_name"] == "brasaland_knowledge"
    assert "query_filter" not in kwargs


def test_query_calls_retrieve_without_profile_kwarg() -> None:
    with (
        patch("pipelines.rag.retrieve", return_value=[]) as retrieve_mock,
        patch("pipelines.rag._generate", return_value="ok"),
    ):
        query("test question")

    retrieve_mock.assert_called_once()
    assert "profile" not in retrieve_mock.call_args.kwargs


def test_staff_default_min_score_is_055() -> None:
    assert DEFAULT_MIN_SCORE == 0.55


def test_setup_missing_source_does_not_delete_collection(tmp_path: Path) -> None:
    for stem in SOURCE_DOCUMENTS[:3]:
        src = CORPUS / f"{stem}.md"
        (tmp_path / f"{stem}.md").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )

    client = MagicMock()
    client.collection_exists.return_value = True

    with (
        patch("pipelines.rag.get_qdrant_client", return_value=client),
        patch("pipelines.rag.embed", return_value=[0.0] * 384),
        pytest.raises(FileNotFoundError),
    ):
        setup(corpus_path=tmp_path)

    client.delete_collection.assert_not_called()


def test_public_rag_does_not_import_support_agent() -> None:
    source = Path(REPO_ROOT / "data" / "pipelines" / "public_rag.py").read_text(
        encoding="utf-8"
    )
    assert "from pipelines.support_agent" not in source
    assert "import support_agent" not in source


def test_support_agent_imports_staff_rag_only() -> None:
    source = Path(REPO_ROOT / "data" / "pipelines" / "support_agent.py").read_text(
        encoding="utf-8"
    )
    assert "from pipelines.rag import" in source
    assert "public_rag" not in source
