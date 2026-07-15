"""Ensure data/ is on sys.path so `pipelines` imports resolve from the data uv env."""

from __future__ import annotations

import sys
from pathlib import Path

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_data_str = str(_DATA_ROOT)
if _data_str not in sys.path:
    sys.path.insert(0, _data_str)
