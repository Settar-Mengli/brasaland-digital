"""Per-dept approval graph interrupt paths (InMemorySaver; mock generate_json)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.approval_graph import build_dept_approval_graph
from pipelines.rfp_intake.response_evaluators import ITERATION_LIMIT

INTERRUPT_KEY = "__interrupt__"


def _as_interrupt_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    return [raw]


def _interrupts(result: Any) -> list[Any]:
    if not isinstance(result, dict):
        return []
    return _as_interrupt_list(result.get(INTERRUPT_KEY))


def _first_interrupt(result: Any) -> Any | None:
    pending = _interrupts(result)
    return pending[0] if pending else None


def _initial(*, department: str = "marketing") -> dict[str, Any]:
    return {
        "department": department,
        "section": {
            "draft_content": f"{department} draft v1",
            "cost": 10.0,
            "setup_days": 12,
            "price_per_cover": None,
        },
        "rework_count": 0,
        "outcome": None,
    }


def test_happy_path_approve() -> None:
    saver = InMemorySaver()
    graph = build_dept_approval_graph(saver)
    config = {"configurable": {"thread_id": "rfp-t1:marketing"}}

    result = graph.invoke(_initial(), config)
    item = _first_interrupt(result)
    assert item is not None
    interrupt_id = str(getattr(item, "id"))

    result = graph.invoke(Command(resume={interrupt_id: "approve"}), config)
    assert _interrupts(result) == []
    assert result.get("outcome") == "approved"
    assert result["section"]["draft_content"] == "marketing draft v1"


def test_reject_regen_reapprove_replaces_draft() -> None:
    saver = InMemorySaver()
    graph = build_dept_approval_graph(saver)
    config = {"configurable": {"thread_id": "rfp-t1:marketing-reject"}}

    def _gen(**_k) -> dict[str, Any]:
        return {
            "draft_content": "marketing draft v2",
            "cost": 11.0,
            "setup_days": 14,
            "price_per_cover": None,
        }

    with patch(
        "pipelines.rfp_intake.approval_graph.generate_json",
        side_effect=_gen,
    ):
        result = graph.invoke(_initial(), config)
        item = _first_interrupt(result)
        assert item is not None
        id1 = str(getattr(item, "id"))

        result = graph.invoke(Command(resume={id1: "reject"}), config)
        pending = _interrupts(result)
        if not pending:
            result = graph.invoke(None, config)
            pending = _interrupts(result)
        assert len(pending) == 1
        payload = getattr(pending[0], "value", {})
        assert payload.get("draft") == "marketing draft v2"
        assert result.get("rework_count") == 1
        assert isinstance(result.get("section"), dict)
        assert result["section"]["draft_content"] == "marketing draft v2"

        id2 = str(getattr(pending[0], "id"))
        result = graph.invoke(Command(resume={id2: "approve"}), config)

    assert _interrupts(result) == []
    assert result.get("outcome") == "approved"
    assert result["section"]["draft_content"] == "marketing draft v2"
    assert result.get("rework_count") == 1


def test_iteration_limit_exhausts() -> None:
    saver = InMemorySaver()
    graph = build_dept_approval_graph(saver)
    config = {"configurable": {"thread_id": "rfp-t1:marketing-exhaust"}}

    def _gen(**_k) -> dict[str, Any]:
        return {
            "draft_content": "marketing draft again",
            "cost": None,
            "setup_days": 12,
            "price_per_cover": None,
        }

    with patch(
        "pipelines.rfp_intake.approval_graph.generate_json",
        side_effect=_gen,
    ):
        result = graph.invoke(_initial(), config)
        for _ in range(ITERATION_LIMIT + 2):
            pending = _interrupts(result)
            if not pending:
                result = graph.invoke(None, config)
                pending = _interrupts(result)
            if not pending:
                break
            if result.get("outcome") == "exhausted":
                break
            interrupt_id = str(getattr(pending[0], "id"))
            result = graph.invoke(Command(resume={interrupt_id: "reject"}), config)

    assert result.get("outcome") == "exhausted"
    assert int(result.get("rework_count") or 0) == ITERATION_LIMIT
