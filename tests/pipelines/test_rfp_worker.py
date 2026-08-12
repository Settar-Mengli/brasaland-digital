"""Department worker + parallel reducer behaviour (LLM mocked)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake.graph import (
    build_intake_graph,
    marketing_worker,
    operaciones_worker,
    procurement_worker,
    training_worker,
)


def test_worker_returns_section_when_needed() -> None:
    state = {
        "departments_needed": ["marketing"],
        "metadata": {"client_name": "Acme", "scope": "catering"},
    }
    with patch(
        "pipelines.rfp_intake.graph.generate_json",
        return_value={"key_aspects": ["brand fit", "volume TBD"]},
    ):
        out = marketing_worker(state)  # type: ignore[arg-type]
    assert len(out["department_sections"]) == 1
    assert out["department_sections"][0]["department_id"] == "marketing"
    assert out["department_sections"][0]["key_aspects"] == ["brand fit", "volume TBD"]


def test_worker_noop_when_not_needed() -> None:
    state = {"departments_needed": ["operaciones"], "metadata": {}}
    with patch("pipelines.rfp_intake.graph.generate_json") as mocked:
        out = marketing_worker(state)  # type: ignore[arg-type]
        mocked.assert_not_called()
    assert out["department_sections"] == []


def test_compiled_graph_reducer_merges_needed_depts_only() -> None:
    """Stub convert→markdown; patch generate_json for classify/extract/workers."""

    def fake_generate(system_prompt: str, user_prompt: str, **kwargs: Any) -> dict:
        if "key_aspects" in system_prompt or "key aspects" in system_prompt.lower():
            dept = "marketing"
            for name in ("marketing", "operaciones", "procurement", "training"):
                if name in system_prompt:
                    dept = name
                    break
            return {"key_aspects": [f"{dept}-aspect"]}
        if "Extract structured" in system_prompt:
            return {
                "client_name": "Stub Co",
                "location": "Medellín",
                "service_type": "catering",
                "scope": "weekly lunch",
                "deadline": None,
                "budget_range": None,
                "open_questions": ["diner count?"],
                "departments_needed": ["marketing", "operaciones"],
            }
        return {"is_valid_rfp": True, "reason": "ok"}

    with (
        patch(
            "pipelines.rfp_intake.graph.convert_node",
            return_value={
                "markdown": (
                    "Scope of work: weekly catering. Budget pricing in USD. "
                    "Service catering for office lunch."
                )
            },
        ),
        patch("pipelines.rfp_intake.graph.generate_json", side_effect=fake_generate),
    ):
        # Build under patches so add_node captures the stubbed convert_node.
        graph = build_intake_graph()
        result = graph.invoke(
            {
                "ticket_id": "t1",
                "rfp_id": "r1",
                "raw_pdf_path": "/tmp/unused.pdf",
            }
        )

    sections = result.get("department_sections") or []
    ids = sorted(s["department_id"] for s in sections)
    assert ids == ["marketing", "operaciones"]
    assert all(s.get("key_aspects") for s in sections)
    # skipped depts must not appear
    assert "procurement" not in ids
    assert "training" not in ids
    assert result.get("summary")


def test_individual_workers_cover_all_four() -> None:
    state = {
        "departments_needed": ["procurement", "training"],
        "metadata": {"scope": "x"},
    }
    with patch(
        "pipelines.rfp_intake.graph.generate_json",
        return_value={"key_aspects": ["a"]},
    ):
        assert operaciones_worker(state)["department_sections"] == []  # type: ignore[arg-type]
        assert len(procurement_worker(state)["department_sections"]) == 1  # type: ignore[arg-type]
        assert len(training_worker(state)["department_sections"]) == 1  # type: ignore[arg-type]
