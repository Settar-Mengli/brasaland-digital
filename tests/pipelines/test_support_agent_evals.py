"""Support-agent evals — assert on TRACE after invoke (mocked I/O for CI)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pipelines.support_agent import (
    REFUSAL_ANSWER,
    TRACES,
    get_trace,
    invoke_support_agent,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOYALTY_DOC = REPO_ROOT / "docs" / "company-knowledge-base" / "loyalty-program.md"

GOLD_LINE = "Gold (50+ points): 15% permanent discount and early access to the seasonal menu before the general public."


def _node_names(run_id: str) -> list[str]:
    trace = get_trace(run_id)
    assert trace is not None
    return [step["node"] for step in trace["nodes"]]


def test_eval_empty_question_skips_retrieve() -> None:
    TRACES.clear()
    result = invoke_support_agent("   ")
    run_id = result["run_id"]
    assert "error" in result
    assert result["error"] == "question must not be empty"

    names = _node_names(run_id)
    assert "validate_question" in names
    assert "retrieve_context" not in names
    assert "generate_answer_node" not in names
    assert "refuse_no_context" not in names
    # MemorySaver requires thread_id on every path including empty.
    assert get_trace(run_id) is not None


def test_eval_no_context_refuses_without_generate() -> None:
    TRACES.clear()
    with patch("pipelines.support_agent.retrieve", return_value=[]) as retrieve_mock:
        result = invoke_support_agent("What is the capital of Mars?")

    retrieve_mock.assert_called_once()
    run_id = result["run_id"]
    assert result.get("answer") == REFUSAL_ANSWER
    assert "error" not in result

    names = _node_names(run_id)
    assert "retrieve_context" in names
    assert "refuse_no_context" in names
    assert "generate_answer_node" not in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["answer"] == REFUSAL_ANSWER


def test_eval_answer_grounded_in_kb() -> None:
    """Path B: CI asserts KB facts on TRACE context (mock retrieve only).

    Live generate_answer grounding is a recon check (gateway env) — see README.
    Generation is stubbed only so the graph can finish offline; grounding proof
    is the injected loyalty-program context on the trace, not the stub answer.
    """
    TRACES.clear()
    loyalty_text = LOYALTY_DOC.read_text(encoding="utf-8")
    assert "50+" in loyalty_text
    assert "15%" in loyalty_text

    injected = [
        {
            "text": GOLD_LINE,
            "source_document": "loyalty-program",
            "section": "Program tiers",
            "company": "brasaland",
            "language": "en",
            "chunk_index": 0,
            "_score": 0.92,
        }
    ]

    with (
        patch("pipelines.support_agent.retrieve", return_value=injected) as retrieve_mock,
        patch(
            "pipelines.support_agent.generate_answer",
            return_value="stub-offline",
        ) as gen_mock,
    ):
        result = invoke_support_agent("How many points for Gold?")

    retrieve_mock.assert_called_once()
    gen_mock.assert_called_once()
    run_id = result["run_id"]
    assert "error" not in result

    names = _node_names(run_id)
    assert "retrieve_context" in names
    assert "generate_answer_node" in names
    assert "refuse_no_context" not in names

    trace = get_trace(run_id)
    assert trace is not None
    context = trace["final"]["context"]
    assert context, "trace must carry retrieved context"
    joined = " ".join(str(c.get("text", "")) for c in context)
    sources = {c.get("source_document") for c in context}
    assert "loyalty-program" in sources
    assert "50+" in joined
    assert "15%" in joined
    # Do not treat the stub answer as grounding proof.
    assert result["answer"] == "stub-offline"
