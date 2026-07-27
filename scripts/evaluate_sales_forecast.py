"""Evaluate graded sales-forecast RF: holdout MAE/RMSE, temporal CV, learning curve.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/evaluate_sales_forecast.py

Features are built once on the full series (run_forecast pattern) so test ``trend``
continues 96..119. CV and learning curve use the TRAIN slice only (2016–2023).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

from pipelines.model_eval import (  # noqa: E402
    compute_learning_curve,
    cross_val_metrics,
    plot_learning_curve,
)
from pipelines.sales_forecast import (  # noqa: E402
    FEATURE_COLUMNS,
    TEST_YEARS,
    TRAIN_YEARS,
    build_features,
    chronological_split,
    fit_naive_rf,
    load_sales,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate RandomForestRegressor(random_state=42): train/test MAE·RMSE, "
            "in-train TimeSeriesSplit CV, learning curve PNG."
        )
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO_ROOT / "data" / "raw" / "brasaland_sales.csv",
        help="Path to brasaland_sales.csv (default: data/raw/brasaland_sales.csv).",
    )
    parser.add_argument(
        "--chart",
        type=Path,
        default=REPO_ROOT / "data" / "eval" / "learning_curve.png",
        help="Output learning-curve PNG (default: data/eval/learning_curve.png).",
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="TimeSeriesSplit n_splits for CV and learning curve (default: 5).",
    )
    args = parser.parse_args()

    data_path = args.data.resolve()
    chart_path = args.chart.resolve()

    df = load_sales(data_path)
    train_df, test_df = chronological_split(df)

    # run_forecast pattern: build once on full series, then slice by year index
    X_all, y_all = build_features(df)
    train_idx = df.index[pd.to_datetime(df["month"]).dt.year.isin(TRAIN_YEARS)]
    test_idx = df.index[pd.to_datetime(df["month"]).dt.year.isin(TEST_YEARS)]

    X_train = X_all.loc[train_idx].reset_index(drop=True)
    y_train = y_all.loc[train_idx].reset_index(drop=True)
    X_test = X_all.loc[test_idx].reset_index(drop=True)
    y_test = y_all.loc[test_idx].reset_index(drop=True)

    assert len(X_train) == 96 and len(X_test) == 24
    assert int(X_train["trend"].iloc[0]) == 0
    assert int(X_train["trend"].iloc[-1]) == 95
    assert int(X_test["trend"].iloc[0]) == 96
    assert int(X_test["trend"].iloc[-1]) == 119

    model = fit_naive_rf(X_train, y_train)
    y_train_pred = model.predict(X_train[list(FEATURE_COLUMNS)])
    y_test_pred = model.predict(X_test[list(FEATURE_COLUMNS)])

    train_mae = float(mean_absolute_error(y_train, y_train_pred))
    train_rmse = float(root_mean_squared_error(y_train, y_train_pred))
    test_mae = float(mean_absolute_error(y_test, y_test_pred))
    test_rmse = float(root_mean_squared_error(y_test, y_test_pred))

    cv = cross_val_metrics(X_train, y_train, n_splits=args.n_splits)
    curve = compute_learning_curve(X_train, y_train, n_splits=args.n_splits)
    plot_learning_curve(curve, chart_path, ylabel="RMSE (USD)")

    print("=== Graded model: naive RandomForestRegressor(random_state=42) ===")
    print(f"Data:  {data_path}")
    print(f"Chart: {chart_path}")
    print(
        f"Train rows: {len(train_df)} (2016–2023)  "
        f"Test rows: {len(test_df)} (2024–2025 holdout)"
    )
    print(
        f"Train max revenue: {float(y_train.max()):.2f}  "
        f"Test max revenue: {float(y_test.max()):.2f}"
    )
    print()
    print("--- TRAIN (fit set) ---")
    print(f"MAE  (USD): {train_mae:.4f}")
    print(f"RMSE (USD): {train_rmse:.4f}")
    print()
    print("--- VALIDATION (in-train TimeSeriesSplit CV; train years only) ---")
    print(f"n_splits: {cv['n_splits']}")
    print(f"MAE  folds: {[round(v, 4) for v in cv['mae_folds']]}")
    print(f"RMSE folds: {[round(v, 4) for v in cv['rmse_folds']]}")
    print(f"MAE  mean±std (USD): {cv['mae_mean']:.4f} ± {cv['mae_std']:.4f}")
    print(f"RMSE mean±std (USD): {cv['rmse_mean']:.4f} ± {cv['rmse_std']:.4f}")
    print()
    print("--- TEST (2024–2025 chronological holdout) ---")
    print(f"MAE  (USD): {test_mae:.4f}")
    print(f"RMSE (USD): {test_rmse:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
