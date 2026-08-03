"""Fix 2 — sentinel Bearer must not appear in trace, checkpoint, or logs."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

from pipelines.support_agent import (
    TRACES,
    get_checkpoint_state,
    get_trace,
    invoke_support_agent,
)
from pipelines.tools.ticket_lookup import TicketLookupResult, TicketRecord

SENTINEL = "SENTINEL_BEARER_DO_NOT_LEAK_9f3a"


def _contains_sentinel(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return SENTINEL in value
    if isinstance(value, (dict, list)):
        return SENTINEL in json.dumps(value, default=str)
    return SENTINEL in str(value)


def test_sentinel_token_absent_from_trace_checkpoint_and_logs(caplog) -> None:
    TRACES.clear()
    incident = TicketRecord(
        id=7,
        source_incident_id="7",
        title="t",
        description="d",
        category="QUEJA_CLIENTE",
        status="open",
        origin="customer",
        branch="COL-01",
        created_at="a",
        updated_at="b",
    )
    tool_result: TicketLookupResult = {
        "ok": True,
        "incidents": [incident],
        "matched_by": "id",
        "error": None,
    }

    with (
        caplog.at_level(logging.DEBUG),
        patch(
            "pipelines.support_agent.lookup_ticket",
            return_value=tool_result,
        ),
    ):
        result = invoke_support_agent(
            "What is the status of ticket 7?",
            access_token=SENTINEL,
            user_id="42",
        )

    run_id = result["run_id"]
    trace = get_trace(run_id)
    assert trace is not None
    assert not _contains_sentinel(trace), "sentinel leaked into get_trace"

    checkpoint = get_checkpoint_state(run_id)
    assert checkpoint is not None
    assert "access_token" not in checkpoint
    assert not _contains_sentinel(checkpoint), "sentinel leaked into checkpoint"

    joined_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert SENTINEL not in joined_logs, "sentinel leaked into log lines"
