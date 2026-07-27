"""Unit tests for chronological sales-forecast split and feature leakage guards."""

from __future__ import annotations

from pathlib import Path

from pipelines.sales_forecast import (
    FEATURE_COLUMNS,
    LEAKAGE_COLUMNS,
    build_features,
    chronological_split,
    load_sales,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SALES_CSV = REPO_ROOT / "data" / "raw" / "brasaland_sales.csv"


def test_chronological_split_and_feature_columns() -> None:
    """Train 2016–2023 / test 2024–2025; no month overlap; no leakage features."""
    df = load_sales(SALES_CSV)
    train, test = chronological_split(df)

    assert len(train) == 96
    assert len(test) == 24

    train_years = set(train["month"].dt.year)
    test_years = set(test["month"].dt.year)
    assert train_years == set(range(2016, 2024))
    assert test_years == set(range(2024, 2026))

    train_months = set(train["month"])
    test_months = set(test["month"])
    assert train_months.isdisjoint(test_months)
    assert train["month"].max() < test["month"].min()

    X, _y = build_features(df)
    assert tuple(X.columns) == FEATURE_COLUMNS
    for col in LEAKAGE_COLUMNS:
        assert col not in X.columns
