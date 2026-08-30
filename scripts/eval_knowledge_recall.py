"""Local-only Recall@3 eval for Brasaland knowledge bases (not CI).

Assumes Qdrant is up and the target collection is already indexed.
Retrieval only — does not call the LLM gateway.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/eval_knowledge_recall.py

Public profile (advisory KPI, always exit 0)::

    uv run --directory data --python 3.13 python ../scripts/eval_knowledge_recall.py --profile public
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
STAFF_EVAL_PATH = DATA_ROOT / "eval" / "test-queries.json"
PUBLIC_EVAL_PATH = DATA_ROOT / "eval" / "public-test-queries.json"
RECALL_AT = 3
STAFF_KPI_PERCENT = 80.0
PUBLIC_KPI_PERCENT = 60.0

if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

load_dotenv(DATA_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")

from pipelines.rag import retrieve  # noqa: E402
from pipelines.rag_profiles import resolve_profile  # noqa: E402


def _run_eval(eval_path: Path, profile_name: str) -> tuple[int, int, float]:
    if not eval_path.is_file():
        raise FileNotFoundError(f"Eval set not found: {eval_path}")

    profile = resolve_profile(profile_name)
    rows = json.loads(eval_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{eval_path} must be a non-empty JSON array")

    hits = 0
    total = len(rows)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{eval_path}[{index}]: expected object, got {type(row).__name__}")
        if "question" not in row:
            raise ValueError(f"{eval_path}[{index}]: missing required field 'question'")
        if "expected_source_document" not in row:
            raise ValueError(
                f"{eval_path}[{index}]: missing required field 'expected_source_document'"
            )

        question = str(row["question"]).strip()
        expected = str(row["expected_source_document"]).strip()
        if not question or not expected:
            raise ValueError(
                f"{eval_path}[{index}]: question and expected_source_document must be non-empty"
            )

        results = retrieve(question, k=RECALL_AT, min_score=0.0, profile=profile)
        top_sources = [str(r.get("source_document", "")) for r in results]
        matched = expected in top_sources
        if matched:
            hits += 1
        status = "HIT" if matched else "MISS"
        print(
            f"[{status}] expected={expected} top3={top_sources!r}\n"
            f"         q={question!r}"
        )

    percent = (100.0 * hits / total) if total else 0.0
    return hits, total, percent


def main() -> int:
    parser = argparse.ArgumentParser(description="Recall@3 eval for knowledge retrieval.")
    parser.add_argument(
        "--profile",
        choices=("staff", "public"),
        default="staff",
        help="Knowledge profile to evaluate (default: staff).",
    )
    args = parser.parse_args()

    if args.profile == "public":
        hits, total, percent = _run_eval(PUBLIC_EVAL_PATH, "public")
        meets = percent >= PUBLIC_KPI_PERCENT
        label = "ADVISORY PASS" if meets else "ADVISORY FAIL"
        print(
            f"\nRecall@{RECALL_AT}: {hits}/{total} = {percent:.1f}% "
            f"({label} advisory KPI >={PUBLIC_KPI_PERCENT:.0f}%)"
        )
        return 0

    hits, total, percent = _run_eval(STAFF_EVAL_PATH, "staff")
    meets = percent >= STAFF_KPI_PERCENT
    print(
        f"\nRecall@{RECALL_AT}: {hits}/{total} = {percent:.1f}% "
        f"({'PASS' if meets else 'FAIL'} KPI >={STAFF_KPI_PERCENT:.0f}%)"
    )
    return 0 if meets else 1


if __name__ == "__main__":
    raise SystemExit(main())
