"""Local-only Recall@3 eval for the Brasaland knowledge base (not CI).

Assumes Qdrant is up and ``brasaland_knowledge`` is already indexed.
Retrieval only — does not call the LLM gateway.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/eval_knowledge_recall.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
EVAL_PATH = DATA_ROOT / "eval" / "test-queries.json"
RECALL_AT = 3
KPI_PERCENT = 80.0

if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

load_dotenv(DATA_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")

from pipelines.rag import retrieve  # noqa: E402


def main() -> int:
    if not EVAL_PATH.is_file():
        raise FileNotFoundError(f"Eval set not found: {EVAL_PATH}")

    rows = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{EVAL_PATH} must be a non-empty JSON array")

    hits = 0
    total = len(rows)
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{EVAL_PATH}[{index}]: expected object, got {type(row).__name__}")
        if "question" not in row:
            raise ValueError(f"{EVAL_PATH}[{index}]: missing required field 'question'")
        if "expected_source_document" not in row:
            raise ValueError(
                f"{EVAL_PATH}[{index}]: missing required field 'expected_source_document'"
            )

        question = str(row["question"]).strip()
        expected = str(row["expected_source_document"]).strip()
        if not question or not expected:
            raise ValueError(
                f"{EVAL_PATH}[{index}]: question and expected_source_document must be non-empty"
            )

        results = retrieve(question, k=RECALL_AT, min_score=0.0)
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
    meets = percent >= KPI_PERCENT
    print(
        f"\nRecall@{RECALL_AT}: {hits}/{total} = {percent:.1f}% "
        f"({'PASS' if meets else 'FAIL'} KPI ≥{KPI_PERCENT:.0f}%)"
    )
    return 0 if meets else 1


if __name__ == "__main__":
    raise SystemExit(main())
