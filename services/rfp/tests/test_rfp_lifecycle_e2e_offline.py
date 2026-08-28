"""Deterministic offline RFP lifecycle E2E through task and approval drivers."""

# DATABASE_URL and the data import path must be initialized before service imports.
# ruff: noqa: E402

from __future__ import annotations

import importlib
import os
import socket
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "sqlite://")
importlib.import_module("config")

import approval_driver
import checkpointer
import pipelines.rfp_intake.approval_graph as approval_graph
import pipelines.rfp_intake.approval_orchestration as approval_orchestration
import pipelines.rfp_intake.generation as generation
import pipelines.rfp_intake.graph as intake_graph
import pipelines.rfp_intake.models as rfp_models
import pipelines.rfp_intake.response_graph as response_graph
import tasks
import upload
from pipelines.rfp_intake.models import FinalDocument
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_final_document,
    get_ticket,
)

DEPARTMENTS = ("marketing", "operaciones")
INITIAL_DRAFTS = {
    "marketing": "Marketing draft v1 covers brand stewardship and launch messaging.",
    "operaciones": "Operations draft v1 covers staffing and a 20-day setup plan.",
}
REGENERATED_FAILING_DRAFT = (
    "Marketing draft v2 is deterministic but intentionally fails compliance."
)


def _evaluation(
    department: str,
    *,
    passes: bool,
    stale_marker: bool = False,
) -> dict[str, Any]:
    compliance: dict[str, Any] = {
        "pass": passes,
        "rule_ids": [] if passes else ["offline-required-brand-term"],
        "violations": [] if passes else ["required brand term is absent"],
    }
    if stale_marker:
        compliance["stale_marker"] = "must-not-survive-regeneration"
    return {
        "department_id": department,
        "readability": {"pass": passes, "score": 80.0 if passes else 20.0},
        "relevance": {"pass": passes, "coverage": 1.0 if passes else 0.0},
        "compliance": compliance,
        "overall_pass": passes,
        "feedback_for_generator": "" if passes else "Add the required brand term.",
        "iterations": 1,
        "exhausted": False,
        "needs_human_review": not passes,
        "ceo_approval_required": False,
    }


@pytest.fixture()
def isolated_engine(tmp_path: Path):
    database_path = tmp_path / "database" / "rfp-e2e.sqlite"
    database_path.parent.mkdir(parents=True)
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(
        dbapi_connection: Any,
        connection_record: Any,
    ) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    tables = [
        rfp_models.Ticket.__table__,
        rfp_models.RfpMetadata.__table__,
        rfp_models.DepartmentSection.__table__,
        rfp_models.FinalDocument.__table__,
    ]
    SQLModel.metadata.create_all(engine, tables=tables)
    try:
        yield engine
    finally:
        engine.dispose()


def test_rfp_lifecycle_is_offline_re_evaluates_regen_and_finalizes_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_engine: Any,
) -> None:
    """Exercise intake through immutable finalization without external state."""
    for name in list(os.environ):
        if name.startswith("GEN_"):
            monkeypatch.delenv(name, raising=False)
    assert not [name for name in os.environ if name.startswith("GEN_")]

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    source_pdf = upload_dir / "offline-rfp.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% offline fixture\n")
    checkpoint_path = tmp_path / "checkpoint" / "rfp.sqlite"
    monkeypatch.setattr(upload, "DATA_RAW", upload_dir)
    monkeypatch.setenv("RFP_CHECKPOINT_PATH", str(checkpoint_path))
    monkeypatch.setattr(tasks, "engine", isolated_engine)
    monkeypatch.setattr(tasks, "ensure_schema", lambda: None)

    def _deny_network(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise AssertionError("offline RFP E2E attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", _deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", _deny_network)
    monkeypatch.setattr(
        generation,
        "generate_json",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError(f"unstubbed generation call: {sorted(kwargs)}")
        ),
    )

    converted_paths: list[str] = []
    intake_generation_calls: list[str] = []

    def _offline_convert(state: dict[str, Any]) -> dict[str, str]:
        raw_path = str(state.get("raw_pdf_path") or "")
        converted_paths.append(raw_path)
        assert Path(raw_path).resolve().is_relative_to(upload_dir.resolve())
        return {
            "markdown": (
                "Commercial catering RFP scope for a New York launch. "
                "The service requires event operations and brand marketing. "
                "Budget: USD 60000. Deadline: 2027-01-15. "
                "The selected supplier will provide a complete implementation plan."
            )
        }

    def _offline_intake_generate(
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        del user_prompt, max_tokens
        if "You classify whether" in system_prompt:
            intake_generation_calls.append("classifier")
            return {"is_valid_rfp": True, "reason": "offline deterministic RFP"}
        if "Extract structured fields" in system_prompt:
            intake_generation_calls.append("metadata")
            return {
                "client_name": "Offline Client",
                "location": "New York",
                "service_type": "Corporate catering",
                "scope": "Launch catering and brand activation",
                "deadline": "2027-01-15",
                "budget_range": "USD 60000",
                "departments_needed": list(DEPARTMENTS),
                "open_questions": [],
            }
        for department in DEPARTMENTS:
            if f"the {department} department" in system_prompt:
                intake_generation_calls.append(department)
                aspects = {
                    "marketing": ["brand stewardship", "launch messaging"],
                    "operaciones": ["staffing plan", "setup timeline"],
                }
                return {"key_aspects": aspects[department]}
        raise AssertionError(f"unexpected intake prompt: {system_prompt[:80]}")

    monkeypatch.setattr(intake_graph, "convert_node", _offline_convert)
    monkeypatch.setattr(intake_graph, "generate_json", _offline_intake_generate)
    monkeypatch.setattr(
        intake_graph,
        "COMPILED_INTAKE_GRAPH",
        intake_graph.build_intake_graph(),
    )

    response_generation_calls: list[str] = []
    response_evaluation_calls: list[tuple[str, str]] = []

    def _offline_response_generate(
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> dict[str, str]:
        del user_prompt, max_tokens
        for department in DEPARTMENTS:
            if f"the {department} department" in system_prompt:
                response_generation_calls.append(department)
                return {"draft_content": INITIAL_DRAFTS[department]}
        raise AssertionError(f"unexpected response prompt: {system_prompt[:80]}")

    def _offline_response_evaluate(
        draft: str,
        key_aspects: list[str],
        budget_range: str | None,
        department: str,
    ) -> dict[str, Any]:
        del key_aspects, budget_range
        response_evaluation_calls.append((department, draft))
        return _evaluation(
            department,
            passes=bool(draft),
            stale_marker=bool(draft),
        )

    monkeypatch.setattr(
        response_graph,
        "generate_json",
        _offline_response_generate,
    )
    monkeypatch.setattr(
        response_graph,
        "evaluate_all",
        _offline_response_evaluate,
    )

    extraction_calls: list[str] = []

    def _offline_extract_generate(
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> dict[str, float | None]:
        del user_prompt, max_tokens
        for department in DEPARTMENTS:
            if f"the {department} department" in system_prompt:
                extraction_calls.append(department)
                return {
                    "cost": 30000.0,
                    "setup_days": 15.0 if department == "marketing" else 20.0,
                    "price_per_cover": 100.0
                    if department == "operaciones"
                    else None,
                }
        raise AssertionError(f"unexpected extraction prompt: {system_prompt[:80]}")

    regen_generation_calls: list[str] = []

    def _offline_regen_generate(
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> dict[str, Any]:
        del user_prompt, max_tokens
        assert "marketing department" in system_prompt
        regen_generation_calls.append("marketing")
        return {
            "draft_content": REGENERATED_FAILING_DRAFT,
            "cost": 30000.0,
            "setup_days": 15.0,
            "price_per_cover": None,
        }

    regen_evaluation_calls: list[tuple[str, list[str], str | None, str]] = []

    def _offline_regen_evaluate(
        draft: str,
        key_aspects: list[str],
        budget_range: str | None,
        department: str,
    ) -> dict[str, Any]:
        regen_evaluation_calls.append(
            (draft, list(key_aspects), budget_range, department)
        )
        assert draft == REGENERATED_FAILING_DRAFT
        return _evaluation(department, passes=False)

    monkeypatch.setattr(
        approval_orchestration,
        "generate_json",
        _offline_extract_generate,
    )
    monkeypatch.setattr(
        approval_graph,
        "generate_json",
        _offline_regen_generate,
    )
    monkeypatch.setattr(
        approval_driver,
        "evaluate_all",
        _offline_regen_evaluate,
    )

    checkpointer.run_setup()
    assert checkpoint_path.is_file()
    assert checkpoint_path.resolve().is_relative_to(tmp_path.resolve())
    assert source_pdf.resolve().is_relative_to(upload.DATA_RAW.resolve())

    with Session(isolated_engine) as session:
        ticket, created = create_ticket(
            session,
            rfp_id="offline-rfp-001",
            content_hash="offline-content-hash-001",
            raw_pdf_path=str(source_pdf),
            owner_user_uuid="offline-owner",
        )
        assert created is True
        ticket_id = ticket.ticket_id

    intake_result = tasks.process_rfp.run(ticket_id)
    assert intake_result == {
        "ticket_id": ticket_id,
        "status": "intake_complete",
        "departments": list(DEPARTMENTS),
        "summary": intake_result["summary"],
    }
    assert intake_result["summary"].startswith("RFP intake summary")
    assert converted_paths == [str(source_pdf)]
    assert Counter(intake_generation_calls) == Counter(
        {"classifier": 1, "metadata": 1, "marketing": 1, "operaciones": 1}
    )

    response_result = tasks.process_rfp_response.run(ticket_id)
    assert response_result == {
        "ticket_id": ticket_id,
        "status": "under_evaluation",
        "departments": list(DEPARTMENTS),
    }
    assert Counter(response_generation_calls) == Counter(DEPARTMENTS)
    assert {
        (department, INITIAL_DRAFTS[department]) for department in DEPARTMENTS
    }.issubset(set(response_evaluation_calls))

    approval_result = tasks.process_rfp_approval.run(ticket_id)
    assert approval_result == {
        "ticket_id": ticket_id,
        "status": "waiting_for_approval",
        "departments": list(DEPARTMENTS),
    }
    assert Counter(extraction_calls) == Counter(DEPARTMENTS)

    with Session(isolated_engine) as session:
        rows = {
            row.department_id: row
            for row in get_department_sections(session, ticket_id)
        }
        for department in DEPARTMENTS:
            assert rows[department].draft_content == INITIAL_DRAFTS[department]
            assert rows[department].evaluation_results["overall_pass"] is True
            assert rows[department].evaluation_results["interrupt_id"]
        assert rows["marketing"].evaluation_results["compliance"][
            "stale_marker"
        ] == "must-not-survive-regeneration"

        reject_result = approval_driver.apply_section_decision(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            action="reject",
            feedback="Regenerate with the required brand language.",
        )
        assert reject_result["outcome"] == "pending_reapproval"
        assert regen_generation_calls == ["marketing"]
        assert regen_evaluation_calls == [
            (
                REGENERATED_FAILING_DRAFT,
                ["brand stewardship", "launch messaging"],
                "USD 60000",
                "marketing",
            )
        ]

        refreshed = {
            row.department_id: row
            for row in get_department_sections(session, ticket_id)
        }["marketing"]
        regenerated_evaluation = dict(refreshed.evaluation_results or {})
        assert refreshed.draft_content == REGENERATED_FAILING_DRAFT
        assert regenerated_evaluation["overall_pass"] is False
        assert regenerated_evaluation["compliance"] == {
            "pass": False,
            "rule_ids": ["offline-required-brand-term"],
            "violations": ["required brand term is absent"],
        }
        assert "stale_marker" not in regenerated_evaluation["compliance"]
        assert regenerated_evaluation["needs_human_review"] is True
        assert regenerated_evaluation["arbitration"]["ceo_approval_required"] is True
        assert regenerated_evaluation["interrupt_id"]

        marketing_approval = approval_driver.apply_section_decision(
            session,
            ticket_id=ticket_id,
            department_id="marketing",
            action="approve",
            feedback=None,
        )
        assert marketing_approval["outcome"] == "approved"
        assert marketing_approval["ceo_pending"] is False

        operations_approval = approval_driver.apply_section_decision(
            session,
            ticket_id=ticket_id,
            department_id="operaciones",
            action="approve",
            feedback=None,
        )
        assert operations_approval["outcome"] == "approved"
        assert operations_approval["status"] == "waiting_for_approval"
        assert operations_approval["ceo_pending"] is True

        ceo_result = approval_driver.apply_ceo_decision(
            session,
            ticket_id=ticket_id,
            action="approve",
        )
        assert ceo_result["ceo_decision"] == "approved"
        assert ceo_result["status"] == "done"
        assert ceo_result["final_document"]["ceo_line"].startswith(
            "CEO approval: Mariana Restrepo"
        )

        ticket = get_ticket(session, ticket_id)
        assert ticket is not None
        assert ticket.status == "done"
        final_row = get_final_document(session, ticket_id)
        assert final_row is not None
        original_final_id = final_row.id
        original_generated_at = final_row.generated_at
        original_final = deepcopy(final_row.document)
        assert original_final == ceo_result["final_document"]
        final_by_department = {
            section["department_id"]: section
            for section in original_final["sections"]
        }
        assert (
            final_by_department["marketing"]["draft_content"]
            == REGENERATED_FAILING_DRAFT
        )

        with pytest.raises(ValueError, match="waiting_for_approval"):
            approval_driver.apply_section_decision(
                session,
                ticket_id=ticket_id,
                department_id="marketing",
                action="approve",
                feedback=None,
            )
        with pytest.raises(ValueError, match="waiting_for_approval"):
            approval_driver.apply_ceo_decision(
                session,
                ticket_id=ticket_id,
                action="approve",
            )
        session.expire_all()
        unchanged = get_final_document(session, ticket_id)
        assert unchanged is not None
        assert unchanged.id == original_final_id
        assert unchanged.generated_at == original_generated_at
        assert unchanged.document == original_final

        session.add(
            FinalDocument(
                ticket_id=ticket_id,
                sections=[],
                total_estimated_value=None,
                document={"tampered": True},
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.expire_all()

        final_rows = session.exec(
            select(FinalDocument).where(FinalDocument.ticket_id == ticket_id)
        ).all()
        assert len(final_rows) == 1
        assert final_rows[0].id == original_final_id
        assert final_rows[0].generated_at == original_generated_at
        assert final_rows[0].document == original_final

    assert not [name for name in os.environ if name.startswith("GEN_")]
