"""Index Brasaland company manuals into Qdrant.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py

Optional::

    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --corpus path/to/docs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

load_dotenv(DATA_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")

from pipelines.rag import resolve_corpus_path, setup  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clear-and-reload brasaland_knowledge Qdrant collection from corpus markdown."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Corpus directory (default: KNOWLEDGE_CORPUS_PATH or docs/company-knowledge-base).",
    )
    args = parser.parse_args()
    corpus = args.corpus.resolve() if args.corpus is not None else resolve_corpus_path()
    summary = setup(corpus_path=corpus)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
