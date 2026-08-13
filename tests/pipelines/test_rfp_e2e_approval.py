"""Reproducible Parts 1→3 approval E2E — programmatic resumes, no LLM/HTTP/UI."""

from __future__ import annotations

import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)

from pipelines.rfp_intake import models as rfp_models  # noqa: F401
from pipelines.rfp_intake.approval_graph import build_dept_approval_graph
from pipelines.rfp_intake.approval_orchestration import (
    apply_arbitration_stamps,
    build_ceo_interrupt_graph,
    extract_all_sections,
    synthesize_final_document,
)
from pipelines.rfp_intake.arbitration import run_arbitration
from pipelines.rfp_intake.graph import DEPARTMENT_OWNERS
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_final_document,
    get_ticket,
    merge_evaluation_results,
    save_department_sections,
    save_final_document,
    save_rfp_metadata,
    update_department_section,
    update_department_section_approval,
    update_ticket_status,
)

INTERRUPT_KEY = "__interrupt__"


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(
        engine,
        tables=[
            rfp_models.Ticket.__table__,
            rfp_models.RfpMetadata.__table__,
            rfp_models.DepartmentSection.__table__,
            rfp_models.FinalDocument.__table__,
        ],
    )
    with Session(engine) as sess:
        yield sess


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


def _first_interrupt_id(result: Any) -> str:
    pending = _interrupts(result)
    assert pending, "expected __interrupt__"
    return str(getattr(pending[0], "id"))


def _fake_generate_json(**kwargs: Any) -> dict[str, Any]:
    system = str(kwargs.get("system_prompt") or "")
    if "revise" in system or "Address the feedback" in system:
        return {
            "draft_content": "marketing draft v2 (regenerated)",
            "cost": 1200.0,
            "setup_days": 14.0,
            "price_per_cover": None,
        }
    # extract path
    if "marketing" in system:
        return {"cost": 1000.0, "setup_days": 12.0, "price_per_cover": None}
    if "operaciones" in system:
        return {"cost": 5000.0, "setup_days": 15.0, "price_per_cover": 25.0}
    return {"cost": None, "setup_days": 12.0, "price_per_cover": None}


def _seed_under_evaluation(session: Session) -> tuple[str, list[str]]:
    rfp_id = str(uuid4())
    ticket, _ = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=f"hash-e2e-{rfp_id}",
        raw_pdf_path="/tmp/e2e.pdf",
    )
    ticket_id = ticket.ticket_id
    update_ticket_status(session, ticket_id, "intake_complete")
    update_ticket_status(session, ticket_id, "drafting")
    update_ticket_status(session, ticket_id, "under_evaluation")

    departments = ["marketing", "operaciones"]
    save_rfp_metadata(
        session,
        rfp_id=rfp_id,
        metadata={
            "client_name": "Acme Catering Co",
            "location": "Medellín",
            "service_type": "catering",
            "budget_range": "USD 80,000 / COP 320,000,000",
            "departments_needed": departments,
            "open_questions": [],
        },
    )
    save_department_sections(
        session,
        ticket_id=ticket_id,
        sections=[
            {
                "department_id": "marketing",
                "key_aspects": ["brand"],
                "draft_content": "marketing draft v1",
                "evaluation_results": {
                    "overall_pass": True,
                    "iterations": 1,
                },
            },
            {
                "department_id": "operaciones",
                "key_aspects": ["staffing"],
                "draft_content": "operaciones draft v1",
                "evaluation_results": {
                    "overall_pass": True,
                    "iterations": 1,
                },
            },
        ],
    )
    return ticket_id, departments


def test_e2e_approval_parts1_to3_simulated_resumes(session: Session) -> None:
    ticket_id, departments = _seed_under_evaluation(session)
    saver = InMemorySaver()
    dept_graph = build_dept_approval_graph(saver)
    ceo_graph = build_ceo_interrupt_graph(saver)

    rows = get_department_sections(session, ticket_id)
    sections: dict[str, dict] = {}
    for row in rows:
        eval_results = dict(row.evaluation_results or {})
        sections[str(row.department_id)] = {
            "draft_content": row.draft_content,
            "key_aspects": row.key_aspects,
            "evaluation_results": eval_results,
        }

    metadata = {
        "client_name": "Acme Catering Co",
        "location": "Medellín",
        "service_type": "catering",
        "budget_range": "USD 80,000 / COP 320,000,000",
        "open_questions": [],
    }

    with (
        patch(
            "pipelines.rfp_intake.approval_orchestration.generate_json",
            side_effect=_fake_generate_json,
        ),
        patch(
            "pipelines.rfp_intake.approval_graph.generate_json",
            side_effect=_fake_generate_json,
        ),
    ):
        numbers = extract_all_sections(sections, departments, metadata)
        for dept, nums in numbers.items():
            merge_evaluation_results(
                session,
                ticket_id=ticket_id,
                department_id=dept,
                patch=dict(nums),
            )
            sections[dept] = {**sections[dept], **dict(nums)}

        arb_raw = run_arbitration(sections=sections, metadata=metadata)
        stamped, arbitration = apply_arbitration_stamps(sections, arb_raw)
        assert arbitration.get("ceo_approval_required") is True

        for dept in departments:
            sec = stamped.get(dept) or {}
            merge_evaluation_results(
                session,
                ticket_id=ticket_id,
                department_id=dept,
                patch={
                    "arbitration": arbitration,
                    **{
                        k: sec.get(k)
                        for k in (
                            "cost",
                            "setup_days",
                            "price_per_cover",
                            "forced_request_changes",
                            "arbiter_feedback",
                        )
                        if k in sec
                    },
                },
            )
            sections[dept] = {**sections[dept], **sec, "arbitration": arbitration}

        update_ticket_status(session, ticket_id, "waiting_for_approval")

        pending: dict[str, str] = {}
        traces: dict[str, list] = {}
        results: dict[str, dict] = {}
        for dept in departments:
            config = {"configurable": {"thread_id": f"rfp-{ticket_id}:{dept}"}}
            result = dept_graph.invoke(
                {
                    "department": dept,
                    "section": dict(sections[dept]),
                    "rework_count": 0,
                    "outcome": None,
                },
                config,
            )
            interrupt_id = _first_interrupt_id(result)
            pending[dept] = interrupt_id
            results[dept] = result
            merge_evaluation_results(
                session,
                ticket_id=ticket_id,
                department_id=dept,
                patch={"interrupt_id": interrupt_id},
            )

        # Reject marketing → regen → re-interrupt (single cycle).
        mkt_cfg = {"configurable": {"thread_id": f"rfp-{ticket_id}:marketing"}}
        result = dept_graph.invoke(
            Command(resume={pending["marketing"]: "reject"}),
            mkt_cfg,
        )
        pending_m = _interrupts(result)
        if not pending_m:
            result = dept_graph.invoke(None, mkt_cfg)
            pending_m = _interrupts(result)
        assert len(pending_m) == 1
        assert result["section"]["draft_content"] == "marketing draft v2 (regenerated)"
        assert int(result.get("rework_count") or 0) == 1
        agents = [
            e.get("agent") for e in (result.get("trace") or []) if isinstance(e, dict)
        ]
        assert "approve" in agents
        assert "regen" in agents
        pending["marketing"] = str(getattr(pending_m[0], "id"))
        sections["marketing"] = dict(result["section"])
        traces["marketing"] = list(result.get("trace") or [])
        mkt_eval = dict(
            next(
                r
                for r in get_department_sections(session, ticket_id)
                if r.department_id == "marketing"
            ).evaluation_results
            or {}
        )
        mkt_eval.update(
            {
                "interrupt_id": pending["marketing"],
                "trace": traces["marketing"][-20:],
                "cost": sections["marketing"].get("cost"),
                "setup_days": sections["marketing"].get("setup_days"),
                "price_per_cover": sections["marketing"].get("price_per_cover"),
            }
        )
        update_department_section(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            draft_content=str(sections["marketing"]["draft_content"]),
            evaluation_results=mkt_eval,
        )

        # Approve both departments (operaciones still on first interrupt).
        for dept in departments:
            cfg = {"configurable": {"thread_id": f"rfp-{ticket_id}:{dept}"}}
            result = dept_graph.invoke(
                Command(resume={pending[dept]: "approve"}),
                cfg,
            )
            assert _interrupts(result) == []
            assert result.get("outcome") == "approved"
            traces[dept] = list(result.get("trace") or [])
            assert traces[dept], f"expected in-state trace for {dept}"
            for entry in traces[dept]:
                assert set(entry) >= {"agent", "input", "output", "timestamp"}
            update_department_section_approval(
                session,
                ticket_id=ticket_id,
                department_id=dept,
                approval_status="approved",
                approver=DEPARTMENT_OWNERS[dept],
                approved_at=datetime.now(UTC),
            )
            merge_evaluation_results(
                session,
                ticket_id=ticket_id,
                department_id=dept,
                patch={
                    "interrupt_id": None,
                    "graph_outcome": "approved",
                    "trace": traces[dept][-20:],
                },
            )
            if result.get("section"):
                sections[dept] = dict(result["section"])

        # CEO interrupt (budget > $50k).
        ceo_cfg = {"configurable": {"thread_id": f"rfp-{ticket_id}:ceo"}}
        ceo_result = ceo_graph.invoke(
            {
                "ticket_id": ticket_id,
                "arbitration": arbitration,
                "ceo_decision": None,
            },
            ceo_cfg,
        )
        ceo_id = _first_interrupt_id(ceo_result)
        ceo_result = ceo_graph.invoke(Command(resume={ceo_id: "approve"}), ceo_cfg)
        assert ceo_result.get("ceo_decision") == "approved"
        ceo_approved_at = ceo_result.get("ceo_approved_at")

        rows = get_department_sections(session, ticket_id)
        approval_outcomes = [
            {
                "department_id": r.department_id,
                "status": r.approval_status,
                "approver": r.approver,
                "approved_at": (
                    r.approved_at.isoformat() if r.approved_at else None
                ),
            }
            for r in rows
        ]
        doc = synthesize_final_document(
            ticket_id=ticket_id,
            sections=sections,
            metadata=metadata,
            arbitration=arbitration,
            ceo_decision="approved",
            departments_needed=departments,
            ceo_approved_at=ceo_approved_at,
            approval_outcomes=approval_outcomes,
        )
        assert doc is not None
        assert doc["header"]["client_name"] == "Acme Catering Co"
        assert doc["header"]["ticket_id"] == ticket_id
        assert [s["department_id"] for s in doc["sections"]] == departments
        assert doc["sections"][0]["owner"] == "Camila Ospina"
        assert doc["sections"][0]["approver"] == "Camila Ospina"
        assert doc["sections"][1]["owner"] == "Felipe Guerrero"
        assert "ceo-threshold" in [
            t.get("id") for t in doc["arbitration_outcomes"]["triggers_fired"]
        ]
        assert doc["ceo_line"] and "Mariana Restrepo" in doc["ceo_line"]
        assert doc["total_estimated_value"] == "USD 80,000 / COP 320,000,000"
        assert "USD" in doc["total_estimated_value"]
        assert "COP" in doc["total_estimated_value"]

        save_final_document(
            session,
            ticket_id=ticket_id,
            sections=doc["sections"],
            total_estimated_value=doc["total_estimated_value"],
            document=doc,
        )
        update_ticket_status(session, ticket_id, "done")

    ticket = get_ticket(session, ticket_id)
    assert ticket is not None
    assert ticket.status == "done"
    stored = get_final_document(session, ticket_id)
    assert stored is not None
    assert isinstance(stored.document, dict)
    assert stored.document["header"]["ticket_id"] == ticket_id
    assert stored.total_estimated_value == "USD 80,000 / COP 320,000,000"

    # Queryable node history after the fact.
    final_rows = {
        str(r.department_id): r for r in get_department_sections(session, ticket_id)
    }
    mkt_trace = (final_rows["marketing"].evaluation_results or {}).get("trace") or []
    ops_trace = (final_rows["operaciones"].evaluation_results or {}).get("trace") or []
    assert any(e.get("agent") == "regen" for e in mkt_trace)
    assert any(e.get("agent") == "approve" for e in ops_trace)
    assert final_rows["marketing"].draft_content == "marketing draft v2 (regenerated)"
