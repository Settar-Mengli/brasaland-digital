"""IDOR / ACL unit coverage for user-scoped memory and traces."""

from __future__ import annotations

from pipelines.memory_store import (
    clear_memory_for_tests,
    force_memory_backend,
    read_memory,
    write_memory,
)
from pipelines.support_agent import TRACES, get_trace, invoke_support_agent


def setup_function() -> None:
    force_memory_backend("memory")
    clear_memory_for_tests()
    TRACES.clear()


def teardown_function() -> None:
    clear_memory_for_tests()
    TRACES.clear()
    force_memory_backend(None)


def test_memory_keys_isolated_per_user() -> None:
    write_memory(
        {
            "location": "miami",
            "category": "hours",
            "summary": "Closes at 10 for user A",
        },
        user_id="user-a",
    )
    write_memory(
        {
            "location": "miami",
            "category": "hours",
            "summary": "Closes at 11 for user B",
        },
        user_id="user-b",
    )
    a = read_memory(user_id="user-a", location="miami", category="hours")
    b = read_memory(user_id="user-b", location="miami", category="hours")
    assert len(a) == 1 and "user A" in a[0]["summary"]
    assert len(b) == 1 and "user B" in b[0]["summary"]
    assert read_memory(user_id="user-c", location="miami") == []


def test_trace_cross_user_denied() -> None:
    result = invoke_support_agent(
        "",
        user_id="owner-1",
        session_id="trace-acl",
    )
    run_id = result["run_id"]
    assert get_trace(run_id, requester_user_uuid="owner-1") is not None
    assert get_trace(run_id, requester_user_uuid="other") is None
    assert (
        get_trace(run_id, requester_user_uuid="other", is_admin=True) is not None
    )
