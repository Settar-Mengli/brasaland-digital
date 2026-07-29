"""Knowledge service configuration and import path for ``data/pipelines``."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# Make ``pipelines`` importable without packaging ``data/`` (package = false).
# Docker sets PYTHONPATH=/app/data; this covers local ``uv run`` from services/knowledge.
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_root_str = str(_DATA_ROOT.resolve())
if _data_root_str not in sys.path:
    sys.path.insert(0, _data_root_str)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
