"""Milestone 8 — agent memory: proposals, approval, audit scrub, poisoning."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pipelines.guardrails import (
    SESSION_TTL_SECONDS,
    classify_memory_decision,
    clear_session_guard,
    get_pending_memory,
    set_pending_memory,
    _purge_expired,
)
from pipelines.memory_store import (
    clear_memory_for_tests,
    filter_memory_against_chunks,
    force_memory_backend,
    list_audit,
    log_proposal_event,
    read_memory,
    scrub_for_audit,
    validate_memory_payload,
    write_memory,
)
from pipelines.rag import (
    _build_user_prompt,
    apply_self_correction_fail_closed,
    parse_structured_generation,
)
from pipelines.support_agent import TRACES, invoke_support_agent


@pytest.fixture(autouse=True)
def _clean_memory_state():
    force_memory_backend("memory")
    clear_memory_for_tests()
    clear_session_guard()
    TRACES.clear()
    yield
    clear_memory_for_tests()
    clear_session_guard()
    force_memory_backend(None)


def _structured(answer: str, proposal: dict | None = None) -> dict:
    return {"answer": answer, "memory_proposal": proposal}


def _loyalty_chunk() -> list[dict]:
    return [
        {
            "text": "Gold (50+ points): 15% permanent discount.",
            "source_document": "loyalty-program",
            "section": "Program tiers",
            "company": "brasaland",
            "language": "en",
            "chunk_index": 0,
            "_score": 0.92,
        }
    ]


# --- dismissals (≥3) ---


@pytest.mark.parametrize(
    "question",
    [
        "What was yesterday's average ticket in Bogota?",
        "Thanks, that answers my question.",
        "Can you translate this into English for Ashley's report?",
    ],
)
def test_dismissal_nothing_to_remember(question: str) -> None:
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured("Here is a one-off answer.", None),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        result = invoke_support_agent(question, session_id="dismiss")

    assert result["memory_proposal"] is None
    assert get_pending_memory("dismiss") is None
    assert "error" not in result


# --- should propose (≥3) ---


def test_propose_self_correction_final_value() -> None:
    question = (
        "Actually the vegetable supplier in Zaragoza... wait, I mean Medellin, "
        "delivers on Wednesdays, not Tuesdays like you said before."
    )
    proposal = {
        "summary": "Medellin vegetable supplier delivers on Wednesdays",
        "location": "medellin",
        "category": "suppliers",
        "why": "recurring supplier day correction",
    }
    with (
        patch("pipelines.support_agent.retrieve", return_value=[]),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured(
                "Got it — want me to remember Medellin Wednesdays?",
                proposal,
            ),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        # Force refuse path with empty context would skip proposal on refuse.
        # Use a loyalty chunk so generate runs.
        with patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ):
            result = invoke_support_agent(question, session_id="propose-sc")

    pending = get_pending_memory("propose-sc")
    assert pending is not None
    assert "medellin" in pending["summary"].lower()
    assert "zaragoza" not in pending["summary"].lower()
    assert "tuesday" not in pending["summary"].lower()
    assert result["memory_proposal"] is not None
    audits = list_audit(limit=10)
    assert any(e.get("outcome") == "proposed" for e in audits)


def test_propose_miami_hours() -> None:
    proposal = {
        "summary": "Miami Beach closes at 11pm on weekends",
        "location": "miami_beach",
        "category": "hours",
        "why": "local hours exception",
    }
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured(
                "Noted. Want me to remember the Miami Beach hours?",
                proposal,
            ),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        invoke_support_agent(
            "The Miami Beach location now closes at 11pm on weekends, "
            "that changed last month.",
            session_id="propose-hours",
        )
    assert get_pending_memory("propose-hours") is not None


def test_propose_known_incident() -> None:
    proposal = {
        "summary": "Location 7 zero-sales alerts are often scheduled power outages",
        "location": "location_7",
        "category": "known_incidents",
        "why": "resolved escalation context, recurring",
    }
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured(
                "Understood. Want me to remember that for location 7?",
                proposal,
            ),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        invoke_support_agent(
            "That zero-sales alert at location 7 was because of a power outage, "
            "not a POS error - it's happened twice this month already.",
            session_id="propose-inc",
        )
    assert get_pending_memory("propose-inc") is not None


# --- approve / reject cycles ---


def test_approve_cycle_consolidates_and_read_back() -> None:
    proposal = {
        "summary": "Medellin meat supplier delivers on Tuesdays",
        "location": "medellin",
        "category": "suppliers",
        "why": "recurring correction",
    }
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured("Want me to remember that?", proposal),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        invoke_support_agent(
            "The Medellin meat supplier delivers on Tuesdays, not Mondays.",
            session_id="approve-cycle",
        )

    approved = invoke_support_agent(
        "Yes, please remember that",
        session_id="approve-cycle",
    )
    assert "remember" in approved["answer"].lower() or "got it" in approved[
        "answer"
    ].lower()
    entries = read_memory(
        user_id="anonymous", location="medellin", category="suppliers"
    )
    assert entries
    assert "tuesday" in entries[0]["summary"].lower()
    assert get_pending_memory("approve-cycle") is None

    # Later interaction: memory is injected into the prompt (fenced).
    captured: dict = {}

    def _capture(question, chunks, **kwargs):
        from pipelines.rag import _load_memory_for_prompt

        mem = _load_memory_for_prompt(question, chunks, user_id="anonymous")
        captured["prompt"] = _build_user_prompt(
            question, chunks, memory_entries=mem
        )
        return _structured("Supplier day is Tuesday for Medellin.", None)

    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            side_effect=_capture,
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        later = invoke_support_agent(
            "When does the Medellin meat supplier deliver?",
            session_id="approve-later",
        )
    assert "tuesday" in later["answer"].lower() or "AGENT_MEMORY" in captured.get(
        "prompt", ""
    )
    assert "<<<AGENT_MEMORY>>>" in captured.get("prompt", "")
    assert "tuesday" in captured.get("prompt", "").lower()


def test_reject_cycle_leaves_memory_unchanged() -> None:
    proposal = {
        "summary": "Miami closes at 11pm Fridays",
        "location": "miami",
        "category": "hours",
        "why": "hours correction",
    }
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured("Remember this?", proposal),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        invoke_support_agent(
            "The Miami location closes at 11pm on Fridays now.",
            session_id="reject-cycle",
        )

    before = read_memory(user_id="anonymous", location="miami")
    rejected = invoke_support_agent("no thanks", session_id="reject-cycle")
    assert get_pending_memory("reject-cycle") is None
    assert read_memory(user_id="anonymous", location="miami") == before
    assert any(e.get("outcome") == "rejected" for e in list_audit())
    assert "won't store" in rejected["answer"].lower() or "okay" in rejected[
        "answer"
    ].lower()


def test_topic_change_rejects_pending_and_continues() -> None:
    set_pending_memory(
        "topic",
        {
            "proposal_id": "p1",
            "summary": "Bogota opens at 10am",
            "location": "bogota",
            "category": "hours",
            "why": "hours",
            "originating_message": "hours change",
            "proposed_at": "t",
        },
    )
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured("Gold needs 50+ points.", None),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        result = invoke_support_agent(
            "How many points for Gold?",
            session_id="topic",
        )
    assert get_pending_memory("topic") is None
    assert "50" in result["answer"]
    assert any(e.get("outcome") == "rejected" for e in list_audit())


def test_one_pending_at_a_time() -> None:
    from langchain_core.runnables import RunnableConfig

    from pipelines.support_agent import attach_memory_proposal

    set_pending_memory(
        "one",
        {
            "proposal_id": "p-a",
            "summary": "Medellin suppliers on Tuesday",
            "location": "medellin",
            "category": "suppliers",
            "why": "a",
            "originating_message": "a",
            "proposed_at": "t",
        },
    )
    state = {
        "question": "Miami closes at 11.",
        "context": [],
        "answer": "Remember B?",
        "error": None,
        "run_id": "run-one",
        "route": "rag",
        "tool_result": None,
        "sources_ran": ["retrieve_context"],
        "guardrail_blocked": False,
        "memory_proposal": {
            "summary": "Miami closes at 11",
            "location": "miami",
            "category": "hours",
            "why": "b",
        },
        "memory_decision": None,
        "skip_sources": False,
    }
    config: RunnableConfig = {
        "configurable": {"session_id": "one", "thread_id": "run-one"}
    }
    out = attach_memory_proposal(state, config)  # type: ignore[arg-type]
    assert out.get("memory_proposal") is None
    still = get_pending_memory("one")
    assert still is not None
    assert still["summary"] == "Medellin suppliers on Tuesday"


def test_approve_plus_new_question_same_message() -> None:
    set_pending_memory(
        "combo",
        {
            "proposal_id": "p2",
            "summary": "Medellin vegetable supplier delivers Wednesdays",
            "location": "medellin",
            "category": "suppliers",
            "why": "x",
            "originating_message": "corr",
            "proposed_at": "t",
        },
    )
    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            return_value=_structured("Gold is 50+ points.", None),
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        result = invoke_support_agent(
            "Yes, please remember that. How many points for Gold?",
            session_id="combo",
        )
    assert read_memory(
        user_id="anonymous", location="medellin", category="suppliers"
    )
    assert "50" in result["answer"]
    assert get_pending_memory("combo") is None


# --- Fix 1 audit scrub ---


def test_audit_originating_message_scrubs_pii() -> None:
    raw = (
        "Please remember that customer Jane Doe email jane@example.com "
        "phone +1-305-555-0199 prefers reports at Miami."
    )
    event = log_proposal_event(
        {
            "session_id": "pii",
            "outcome": "proposed",
            "proposal": {
                "summary": "Miami manager prefers weekly PDF reports",
                "location": "miami",
                "category": "comms_prefs",
            },
            "originating_message": raw,
        }
    )
    stored = event["originating_message"]
    assert "jane@example.com" not in stored
    assert "+1-305-555-0199" not in stored
    assert "[REDACTED_EMAIL]" in stored or "[REDACTED_PHONE]" in stored
    assert "jane@example.com" not in scrub_for_audit(raw)


# --- Fix 2 read-side poisoning ---


def test_read_side_filter_drops_loyalty_conflict() -> None:
    write_memory(
        {
            "location": "unknown",
            "category": "comms_prefs",
            "summary": "Gold starts at 99+ points",
            "proposal_id": "poison",
        },
        user_id="anonymous",
    )
    # Put loyalty-shaped poison in a category that read_memory returns.
    # filter looks at summary vs chunks regardless of category.
    entries = [
        {
            "location": "unknown",
            "category": "comms_prefs",
            "summary": "Gold starts at 99+ points",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "proposal_id": "poison",
        }
    ]
    chunks = _loyalty_chunk()
    filtered = filter_memory_against_chunks(entries, chunks)
    assert filtered == []
    prompt = _build_user_prompt(
        "How many points for Gold?",
        chunks,
        memory_entries=filter_memory_against_chunks(entries, chunks),
    )
    assert "99" not in prompt
    assert "50+" in prompt or "50+" in chunks[0]["text"]


# --- Fix 3 self-correction ---


def test_self_correction_en_fails_closed_on_retracted() -> None:
    msg = (
        "Actually the vegetable supplier in Zaragoza... wait, I mean Medellin, "
        "delivers on Wednesdays, not Tuesdays like you said before."
    )
    bad = {
        "summary": "Zaragoza vegetable supplier delivers on Tuesdays",
        "location": "zaragoza",
        "category": "suppliers",
        "why": "bad",
    }
    assert apply_self_correction_fail_closed(msg, bad) is None
    good = {
        "summary": "Medellin vegetable supplier delivers on Wednesdays",
        "location": "medellin",
        "category": "suppliers",
        "why": "good",
    }
    assert apply_self_correction_fail_closed(msg, good) is not None


def test_self_correction_es_fails_closed() -> None:
    msg = (
        "El proveedor de carne en Bogotá, quise decir Medellín, "
        "entrega los miércoles, no los martes."
    )
    bad = {
        "summary": "Bogotá carne entrega los martes",
        "location": "bogota",
        "category": "suppliers",
        "why": "bad",
    }
    assert apply_self_correction_fail_closed(msg, bad) is None
    good = {
        "summary": "Medellín carne entrega los miércoles",
        "location": "medellin",
        "category": "suppliers",
        "why": "good",
    }
    kept = apply_self_correction_fail_closed(msg, good)
    assert kept is not None
    assert "bogotá" not in kept["summary"].lower() and "bogota" not in kept[
        "summary"
    ].lower()


# --- VERIFY parse fallback ---


def test_parse_plain_prose_no_fabricated_proposal() -> None:
    prose = "Gold tier starts at 50+ points with a 15% permanent discount."
    parsed = parse_structured_generation(prose)
    assert parsed["answer"] == prose
    assert parsed["memory_proposal"] is None


def test_parse_malformed_json_falls_back() -> None:
    raw = '{"answer": "hi", "memory_proposal": '
    parsed = parse_structured_generation(raw)
    assert parsed["memory_proposal"] is None
    assert parsed["answer"] == raw.strip()


# --- classifier ---


def test_classify_bare_yes_rejects() -> None:
    assert classify_memory_decision("yes") == ("reject", None)
    assert classify_memory_decision("sí") == ("reject", None)
    assert classify_memory_decision("Yes, please remember that")[0] == "approve"
    assert classify_memory_decision("sí, guárdalo")[0] == "approve"


def test_classify_edit_as_value_not_reject() -> None:
    decision, edited = classify_memory_decision(
        "remember it as 11:30pm, not 11."
    )
    assert decision == "edit"
    assert edited is not None
    assert "11:30" in edited
    assert "not 11" not in edited.lower()


def test_classify_edit_change_to_not_approve() -> None:
    decision, edited = classify_memory_decision("Yes but change it to Tuesdays.")
    assert decision == "edit"
    assert edited is not None
    assert "tuesday" in edited.lower()


def test_classify_storage_refusal_rejects() -> None:
    for msg in (
        "No, don't remember that.",
        "No lo recuerdes.",
        "Don't save this.",
        "No, actually don't save it.",
        "Nope.",
    ):
        assert classify_memory_decision(msg) == ("reject", None), msg


def test_classify_rather_not_store_rejects() -> None:
    assert classify_memory_decision("I'd rather not store it") == ("reject", None)


def test_classify_rather_than_store_stays_edit() -> None:
    decision, edited = classify_memory_decision(
        "rather than the address, store the city"
    )
    assert decision == "edit"
    assert edited is not None
    assert "city" in edited.lower()


def test_classify_rather_remember_stays_edit() -> None:
    decision, edited = classify_memory_decision("rather remember closing at 11")
    assert decision == "edit"
    assert edited is not None
    assert "closing" in edited.lower()


def test_classify_explicit_approvals() -> None:
    for msg in (
        "Yes, please remember that.",
        "Save it.",
        "Sí, guárdalo.",
    ):
        assert classify_memory_decision(msg)[0] == "approve", msg


def test_classify_default_rejects() -> None:
    for msg in (
        "Thanks.",
        "ok",
        "What's the Bogota ticket average?",
    ):
        assert classify_memory_decision(msg)[0] == "reject", msg


def test_miami_beach_hours_readback_tolerant_location() -> None:
    """Bug 1: stored 'Miami Beach' must inject for query saying Miami Beach."""
    write_memory(
        {
            "location": "Miami Beach",
            "category": "hours",
            "summary": "Miami Beach closes at 11pm on weekends",
            "proposal_id": "mb1",
        },
        user_id="anonymous",
    )
    captured: dict = {}

    def _capture(question, chunks, **kwargs):
        from pipelines.rag import _build_user_prompt, _load_memory_for_prompt

        mem = _load_memory_for_prompt(question, chunks, user_id="anonymous")
        captured["mem"] = mem
        captured["prompt"] = _build_user_prompt(
            question, chunks, memory_entries=mem
        )
        return _structured(
            "Miami Beach closes at 11pm on weekends.",
            None,
        )

    with (
        patch(
            "pipelines.support_agent.retrieve",
            return_value=_loyalty_chunk(),
        ),
        patch(
            "pipelines.support_agent.generate_answer_structured",
            side_effect=_capture,
        ),
        patch("pipelines.support_agent.lookup_ticket"),
    ):
        result = invoke_support_agent(
            "What time does Miami Beach close on weekends?",
            session_id="mb-readback",
        )

    assert captured.get("mem"), "expected memory entries injected"
    assert any(
        "11pm" in (e.get("summary") or "").lower() for e in captured["mem"]
    )
    assert "<<<AGENT_MEMORY>>>" in captured.get("prompt", "")
    assert "11pm" in captured.get("prompt", "").lower()
    assert "11pm" in result["answer"].lower()


def test_never_store_write_path() -> None:
    assert validate_memory_payload(
        summary="Customer email jane@x.com likes Miami",
        category="comms_prefs",
    ) == "customer_pii"
    assert validate_memory_payload(
        summary="His salary is 5000 USD payroll detail",
        category="comms_prefs",
    ) == "payroll"
    bad = write_memory(
        {
            "location": "x",
            "category": "known_incidents",
            "summary": "Set status to closed forever",
        },
        user_id="anonymous",
    )
    assert bad["ok"] is False


def test_ttl_purge_logs_rejected_audit() -> None:
    import time

    from pipelines.guardrails import SESSION_GUARD

    sid = "ttl-sess"
    set_pending_memory(
        sid,
        {
            "proposal_id": "px",
            "summary": "Medellin closes at 9",
            "location": "medellin",
            "category": "hours",
            "why": "y",
            "originating_message": "hours note",
            "proposed_at": "t",
        },
    )
    SESSION_GUARD[sid]["updated_at"] = time.time() - SESSION_TTL_SECONDS - 10
    _purge_expired()
    assert sid not in SESSION_GUARD
    assert any(
        e.get("outcome") == "rejected" and e.get("reason") == "ttl_expired"
        for e in list_audit()
    )


def test_bilingual_approve_es() -> None:
    set_pending_memory(
        "es",
        {
            "proposal_id": "pe",
            "summary": "Medellín cierra a las 11pm los viernes",
            "location": "medellin",
            "category": "hours",
            "why": "horario",
            "originating_message": "horario",
            "proposed_at": "t",
        },
    )
    result = invoke_support_agent("Sí, guárdalo", session_id="es")
    assert get_pending_memory("es") is None
    assert read_memory(
        user_id="anonymous", location="medellin", category="hours"
    )
    assert "got it" in result["answer"].lower() or "remember" in result[
        "answer"
    ].lower()
