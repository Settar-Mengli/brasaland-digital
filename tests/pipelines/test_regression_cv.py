"""Unit tests: temporal CV folds preserve chronological order (no shuffle)."""

from __future__ import annotations

from pathlib import Path

from pipelines.model_eval import make_time_series_folds
from pipelines.sales_forecast import build_features, chronological_split, load_sales

REPO_ROOT = Path(__file__).resolve().parents[2]
SALES_CSV = REPO_ROOT / "data" / "raw" / "brasaland_sales.csv"


def test_time_series_folds_preserve_chronological_order() -> None:
    """n_splits >= 5; every fold has max(train_idx) < min(val_idx)."""
    df = load_sales(SALES_CSV)
    train, _test = chronological_split(df)
    X, y = build_features(train)

    n_splits = 5
    tscv = make_time_series_folds(X, y, n_splits=n_splits)
    assert tscv.n_splits >= 5

    folds = list(tscv.split(X))
    assert len(folds) == n_splits
    for train_idx, val_idx in folds:
        assert len(train_idx) > 0
        assert len(val_idx) > 0
        assert max(train_idx) < min(val_idx)
