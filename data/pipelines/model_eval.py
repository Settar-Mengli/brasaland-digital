"""Temporal CV and learning-curve helpers for the graded sales-forecast RF.

Callers must pass features built once (full series, then train slice) so `trend`
stays a global calendar index. This module never calls build_features on fold
subsets — that would reset trend to 0.

CV and learning-curve helpers operate on the TRAIN years only. Graded path:
fit_naive_rf / RandomForestRegressor(random_state=42).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, learning_curve

from pipelines.sales_forecast import FEATURE_COLUMNS, fit_naive_rf


def make_time_series_folds(
    X: pd.DataFrame, y: pd.Series, n_splits: int = 5
) -> TimeSeriesSplit:
    """Return TimeSeriesSplit (never shuffles); folds slice X/y by position."""
    if len(X) != len(y):
        raise ValueError("make_time_series_folds: X and y length mismatch")
    return TimeSeriesSplit(n_splits=n_splits)


def cross_val_metrics(
    X: pd.DataFrame, y: pd.Series, n_splits: int = 5
) -> dict[str, Any]:
    """MAE and RMSE per validation fold + mean±std; graded fit_naive_rf only.

    Expects X/y already built once for the chronological TRAIN frame (no
    rebuild per fold). Inner folds are labeled validation (not test).
    """
    tscv = make_time_series_folds(X, y, n_splits=n_splits)
    mae_folds: list[float] = []
    rmse_folds: list[float] = []

    for train_idx, val_idx in tscv.split(X):
        X_tr = X.iloc[train_idx]
        y_tr = y.iloc[train_idx]
        X_val = X.iloc[val_idx]
        y_val = y.iloc[val_idx]

        model = fit_naive_rf(X_tr, y_tr)
        y_pred = model.predict(X_val[list(FEATURE_COLUMNS)])
        mae_folds.append(float(mean_absolute_error(y_val, y_pred)))
        rmse_folds.append(float(root_mean_squared_error(y_val, y_pred)))

    mae_arr = np.asarray(mae_folds, dtype=float)
    rmse_arr = np.asarray(rmse_folds, dtype=float)
    return {
        "n_splits": n_splits,
        "mae_folds": mae_folds,
        "rmse_folds": rmse_folds,
        "mae_mean": float(mae_arr.mean()),
        "mae_std": float(mae_arr.std(ddof=0)),
        "rmse_mean": float(rmse_arr.mean()),
        "rmse_std": float(rmse_arr.std(ddof=0)),
    }


def compute_learning_curve(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    n_splits: int = 5,
    train_sizes: np.ndarray | None = None,
    scoring: str = "neg_root_mean_squared_error",
) -> dict[str, Any]:
    """Train/validation error curves via learning_curve + explicit TimeSeriesSplit.

    Never uses sklearn's default CV. Scores are negated to positive error.
    Operates on TRAIN-years X/y only. Graded estimator: fit_naive_rf.
    """
    if train_sizes is None:
        train_sizes = np.linspace(0.2, 1.0, 5)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    # Same graded constructor as fit_naive_rf; learning_curve needs an unfitted estimator.
    estimator = RandomForestRegressor(random_state=42)

    sizes, train_scores, val_scores = learning_curve(
        estimator,
        X[list(FEATURE_COLUMNS)],
        y,
        cv=tscv,
        train_sizes=train_sizes,
        scoring=scoring,
        shuffle=False,
    )
    return {
        "train_sizes": sizes,
        "train_errors": -np.asarray(train_scores, dtype=float),
        "validation_errors": -np.asarray(val_scores, dtype=float),
        "scoring": scoring,
        "n_splits": n_splits,
    }


def plot_learning_curve(
    curve: dict[str, Any],
    chart_path: Path,
    *,
    ylabel: str = "RMSE (USD)",
) -> None:
    """Save train vs validation learning-curve PNG (lazy matplotlib; headless-safe)."""
    import matplotlib.pyplot as plt  # lazy: keep module import headless-CI safe

    chart_path.parent.mkdir(parents=True, exist_ok=True)
    sizes = np.asarray(curve["train_sizes"], dtype=float)
    train_err = np.asarray(curve["train_errors"], dtype=float)
    val_err = np.asarray(curve["validation_errors"], dtype=float)

    train_mean = train_err.mean(axis=1)
    train_std = train_err.std(axis=1)
    val_mean = val_err.mean(axis=1)
    val_std = val_err.std(axis=1)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(
        sizes,
        train_mean - train_std,
        train_mean + train_std,
        alpha=0.2,
        color="#c45c26",
    )
    ax.fill_between(
        sizes,
        val_mean - val_std,
        val_mean + val_std,
        alpha=0.2,
        color="#2f6f4e",
    )
    ax.plot(sizes, train_mean, "o-", color="#c45c26", label="Train error")
    ax.plot(
        sizes,
        val_mean,
        "o-",
        color="#2f6f4e",
        label="Validation error (TimeSeriesSplit)",
    )
    ax.set_title("Learning curve — graded RF (train years 2016–2023 only)")
    ax.set_xlabel("Training examples")
    ax.set_ylabel(ylabel)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.text(
        0.5,
        0.01,
        "Validation folds are in-train TimeSeriesSplit only; 2024–2025 test holdout is excluded.",
        ha="center",
        va="bottom",
        fontsize=8,
        wrap=True,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(chart_path, dpi=120)
    plt.close(fig)
