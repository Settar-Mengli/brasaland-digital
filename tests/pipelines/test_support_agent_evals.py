"""Support-agent evals — assert on TRACE after invoke (mocked I/O for CI)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pipelines.support_agent import (
    REFUSAL_ANSWER,
    TICKET_FALLBACK_ANSWER,
    TRACES,
    get_trace,
    invoke_support_agent,
)
from pipelines.tools.ticket_lookup import TicketLookupResult, TicketRecord

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


def _sample_incident(*, ticket_id: int = 7, source_id: str = "7") -> TicketRecord:
    return TicketRecord(
        id=ticket_id,
        source_incident_id=source_id,
        title="Cold fries complaint",
        description="Guest reported cold fries",
        category="QUEJA_CLIENTE",
        status="in_progress",
        origin="customer",
        branch="COL-01",
        created_at="2026-01-15T12:00:00+00:00",
        updated_at="2026-01-16T09:30:00+00:00",
    )


def test_eval_ticket_status_uses_tool_not_rag() -> None:
    TRACES.clear()
    incident = _sample_incident()
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "id",
        "error": None,
    }

    with (
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ) as lookup_mock,
        patch("pipelines.support_agent.retrieve") as retrieve_mock,
    ):
        result = invoke_support_agent("What is the status of ticket 7?")

    lookup_mock.assert_called_once()
    retrieve_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result
    assert "in_progress" in result["answer"]
    assert "QUEJA_CLIENTE" in result["answer"]

    names = _node_names(run_id)
    assert "lookup_ticket" in names
    assert "retrieve_context" not in names
    assert "compose_answer" in names
    assert "route_sources" in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "tool"
    assert trace["final"]["sources_ran"] == ["ticket_lookup"]


def test_eval_kb_question_uses_rag_not_tool() -> None:
    TRACES.clear()
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
        ),
        patch("pipelines.support_agent.lookup_ticket") as lookup_mock,
    ):
        result = invoke_support_agent("How many points for Gold?")

    retrieve_mock.assert_called_once()
    lookup_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result

    names = _node_names(run_id)
    assert "retrieve_context" in names
    assert "lookup_ticket" not in names
    assert "generate_answer_node" in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "rag"
    assert trace["final"]["sources_ran"] == ["retrieve_context"]


def test_eval_ticket_tool_unavailable_honest_fallback() -> None:
    TRACES.clear()
    failed: TicketLookupResult = {
        "ok": False,
        "incidents": [],
        "matched_by": None,
        "error": "incident-manager request timed out",
    }

    with patch(
        "pipelines.support_agent.lookup_ticket",
        return_value=failed,
    ) as lookup_mock:
        result = invoke_support_agent("What is the status of ticket 99?")

    lookup_mock.assert_called_once()
    run_id = result["run_id"]
    assert result.get("answer") == TICKET_FALLBACK_ANSWER
    assert "error" not in result
    assert "resolved" not in result["answer"].lower()
    assert "open" not in result["answer"].lower()
    assert "in_progress" not in result["answer"].lower()

    names = _node_names(run_id)
    assert "lookup_ticket" in names
    assert "compose_answer" in names

    trace = get_trace(run_id)
    assert trace is not None
    lookup_step = next(s for s in trace["nodes"] if s["node"] == "lookup_ticket")
    assert lookup_step["ok"] is False
    assert trace["final"]["sources_ran"] == []
    assert "ticket_lookup" not in trace["final"]["sources_ran"]


def test_eval_ticket_resolves_via_source_incident_id_after_404() -> None:
    """Numeric ref resolved via source_incident_id (MCP adapter returns matched_by)."""
    TRACES.clear()
    incident = _sample_incident(ticket_id=12, source_id="482")
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "source_incident_id",
        "error": None,
    }

    with (
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ) as lookup_mock,
        patch("pipelines.support_agent.retrieve") as retrieve_mock,
    ):
        result = invoke_support_agent("What is the status of ticket 482?")

    lookup_mock.assert_called_once()
    retrieve_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result
    assert "in_progress" in result["answer"]
    assert "482" in result["answer"]

    names = _node_names(run_id)
    assert "lookup_ticket" in names
    assert "retrieve_context" not in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "tool"
    assert trace["final"]["sources_ran"] == ["ticket_lookup"]
    assert trace["final"].get("matched_by") == "source_incident_id"
    lookup_step = next(s for s in trace["nodes"] if s["node"] == "lookup_ticket")
    assert lookup_step["ok"] is True
    assert lookup_step["matched_by"] == "source_incident_id"


def test_eval_parse_alphanumeric_ticket_ref() -> None:
    from pipelines.support_agent import _parse_ticket_input

    inp = _parse_ticket_input("What is the status of ticket MANUAL-98?")
    assert inp.get("ticket_ref") == "MANUAL-98"


def test_eval_alphanumeric_ticket_routes_tool_only() -> None:
    """MANUAL-98 must not trip RAG (hyphenated manual) — tool-only path."""
    TRACES.clear()
    incident = _sample_incident(ticket_id=98, source_id="MANUAL-98")
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "source_incident_id",
        "error": None,
    }

    with (
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ) as lookup_mock,
        patch("pipelines.support_agent.retrieve") as retrieve_mock,
    ):
        result = invoke_support_agent("What is the status of ticket MANUAL-98?")

    lookup_mock.assert_called_once()
    called_inp = lookup_mock.call_args[0][0]
    assert called_inp.get("ticket_ref") == "MANUAL-98"
    retrieve_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result
    assert "in_progress" in result["answer"]
    assert "MANUAL-98" in result["answer"]

    names = _node_names(run_id)
    assert "lookup_ticket" in names
    assert "retrieve_context" not in names
    assert "compose_answer" in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "tool"
    assert trace["final"]["sources_ran"] == ["ticket_lookup"]


def test_eval_alphanumeric_ref_skips_by_id_matches_source() -> None:
    """Non-numeric ref resolves via source_incident_id through MCP adapter."""
    TRACES.clear()
    incident = _sample_incident(ticket_id=98, source_id="MANUAL-98")
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "source_incident_id",
        "error": None,
    }

    with (
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ) as lookup_mock,
        patch("pipelines.support_agent.retrieve") as retrieve_mock,
    ):
        result = invoke_support_agent("What is the status of ticket MANUAL-98?")

    called_inp = lookup_mock.call_args[0][0]
    assert called_inp.get("ticket_ref") == "MANUAL-98"
    retrieve_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result
    assert "in_progress" in result["answer"]
    assert "MANUAL-98" in result["answer"]

    names = _node_names(run_id)
    assert "lookup_ticket" in names
    assert "retrieve_context" not in names

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "tool"
    assert trace["final"]["sources_ran"] == ["ticket_lookup"]
    assert trace["final"].get("matched_by") == "source_incident_id"
    lookup_step = next(s for s in trace["nodes"] if s["node"] == "lookup_ticket")
    assert lookup_step["ok"] is True
    assert lookup_step["matched_by"] == "source_incident_id"


def test_eval_numeric_ticket_resolves_by_id() -> None:
    """Regression: ticket 98 matched_by=id via MCP adapter."""
    TRACES.clear()
    incident = _sample_incident(ticket_id=98, source_id="MANUAL-98")
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "id",
        "error": None,
    }

    with (
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ),
        patch("pipelines.support_agent.retrieve") as retrieve_mock,
    ):
        result = invoke_support_agent("What is the status of ticket 98?")

    retrieve_mock.assert_not_called()
    run_id = result["run_id"]
    assert "error" not in result
    assert "in_progress" in result["answer"]

    trace = get_trace(run_id)
    assert trace is not None
    assert trace["final"]["route"] == "tool"
    assert trace["final"]["sources_ran"] == ["ticket_lookup"]
    assert trace["final"].get("matched_by") == "id"
    lookup_step = next(s for s in trace["nodes"] if s["node"] == "lookup_ticket")
    assert lookup_step["matched_by"] == "id"
