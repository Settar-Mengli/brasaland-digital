"""Index Brasaland knowledge manuals into Qdrant.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py

Optional::

    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --corpus path/to/docs
    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --profile public
    uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --validate-only
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
from pipelines.rag_profiles import resolve_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clear-and-reload Brasaland Qdrant knowledge collection from corpus."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Corpus directory (default: profile-specific corpus path).",
    )
    parser.add_argument(
        "--profile",
        choices=("staff", "public"),
        default="staff",
        help="Knowledge profile to index (default: staff).",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate sources and chunk counts without writing to Qdrant.",
    )
    args = parser.parse_args()
    profile = resolve_profile(args.profile)
    corpus = (
        args.corpus.resolve()
        if args.corpus is not None
        else resolve_corpus_path(profile=profile)
    )
    summary = setup(
        corpus_path=corpus,
        profile=profile,
        validate_only=args.validate_only,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
