"""Prove Annotated[list, operator.add] merges parallel department appends."""

from __future__ import annotations

import operator
import sys
from pathlib import Path
from typing import Annotated, Any, TypedDict
from unittest.mock import patch

from langgraph.graph import END, START, StateGraph

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.graph import marketing_worker, operaciones_worker


class _FanInState(TypedDict, total=False):
    departments_needed: list[str]
    metadata: dict
    department_sections: Annotated[list[dict], operator.add]


def test_two_parallel_workers_merge_to_two_sections() -> None:
    builder: StateGraph = StateGraph(_FanInState)
    builder.add_node("marketing_worker", marketing_worker)
    builder.add_node("operaciones_worker", operaciones_worker)

    def _join(state: _FanInState) -> dict[str, Any]:
        return {}

    builder.add_node("join", _join)
    builder.add_edge(START, "marketing_worker")
    builder.add_edge(START, "operaciones_worker")
    builder.add_edge("marketing_worker", "join")
    builder.add_edge("operaciones_worker", "join")
    builder.add_edge("join", END)
    graph = builder.compile()

    with patch(
        "pipelines.rfp_intake.graph.generate_json",
        return_value={"key_aspects": ["x"]},
    ):
        result = graph.invoke(
            {
                "departments_needed": ["marketing", "operaciones"],
                "metadata": {"scope": "test"},
            }
        )

    sections = result["department_sections"]
    assert len(sections) == 2
    ids = {s["department_id"] for s in sections}
    assert ids == {"marketing", "operaciones"}
