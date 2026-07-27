"""Sales forecasting: chronological RF for consolidated monthly revenue.

Graded model: RandomForestRegressor(random_state=42) on time-derived features
only. Stakeholder is Finance / Mariana — an explainable number beats a black-box
accuracy edge. XGBoost is not used: test years already exceed the training max
(~994k vs ~889k), and no tree ensemble extrapolates above its training leaves,
so XGBoost's accuracy advantage is structurally neutralized here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, roc_auc_score

FEATURE_COLUMNS: tuple[str, ...] = ("trend", "month_sin", "month_cos", "year")
TARGET_COLUMN = "revenue_usd"
LEAKAGE_COLUMNS: tuple[str, ...] = ("covers_served", "avg_ticket_usd")
TRAIN_YEARS = range(2016, 2024)
TEST_YEARS = range(2024, 2026)


def load_sales(path: Path) -> pd.DataFrame:
    """Load and sort sales CSV; guard that month and revenue_usd are present."""
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)

    if df["month"].isna().any():
        raise ValueError(
            "load_sales: column 'month' has null or empty values "
            f"({int(df['month'].isna().sum())} rows)"
        )
    if df[TARGET_COLUMN].isna().any():
        raise ValueError(
            "load_sales: column 'revenue_usd' has null or empty values "
            f"({int(df[TARGET_COLUMN].isna().sum())} rows)"
        )
    if (df[TARGET_COLUMN].astype(str).str.strip() == "").any():
        raise ValueError("load_sales: column 'revenue_usd' has empty-string values")

    return df


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build time-derived features; exclude covers_served / avg_ticket_usd (leakage)."""
    month = pd.to_datetime(df["month"])
    month_of_year = month.dt.month.astype(float)
    angle = 2.0 * np.pi * month_of_year / 12.0

    X = pd.DataFrame(
        {
            "trend": np.arange(len(df), dtype=int),
            "month_sin": np.sin(angle),
            "month_cos": np.cos(angle),
            "year": month.dt.year.astype(int),
        },
        index=df.index,
    )
    assert list(X.columns) == list(FEATURE_COLUMNS)
    for col in LEAKAGE_COLUMNS:
        assert col not in X.columns

    y = df[TARGET_COLUMN].astype(float)
    return X, y


def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological train (2016–2023) / test (2024–2025); no shuffle."""
    years = pd.to_datetime(df["month"]).dt.year
    train = df.loc[years.isin(TRAIN_YEARS)].copy().reset_index(drop=True)
    test = df.loc[years.isin(TEST_YEARS)].copy().reset_index(drop=True)
    return train, test


def fit_naive_rf(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Fit the graded Random Forest (reproducible; explainable over XGBoost)."""
    # RF over XGBoost: Finance/Mariana needs an explainable number; test max
    # (~994k) exceeds train max (~889k), so no tree ensemble extrapolates past
    # training leaves — XGBoost's accuracy edge is neutralized on this dataset.
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train[list(FEATURE_COLUMNS)], y_train)
    return model


@dataclass(frozen=True)
class TrendAwareModel:
    """Productionization-only: linear trend + RF on seasonal residual."""

    trend_model: LinearRegression
    residual_rf: RandomForestRegressor

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        trend = X[["trend"]]
        y_trend = self.trend_model.predict(trend)
        residual = self.residual_rf.predict(X[list(FEATURE_COLUMNS)])
        return y_trend + residual


def fit_trend_aware_rf(X_train: pd.DataFrame, y_train: pd.Series) -> TrendAwareModel:
    """Productionization analysis only — does not replace the graded naive RF."""
    trend_model = LinearRegression()
    trend_model.fit(X_train[["trend"]], y_train)
    y_trend = trend_model.predict(X_train[["trend"]])
    residual = y_train.to_numpy(dtype=float) - y_trend
    residual_rf = RandomForestRegressor(random_state=42)
    residual_rf.fit(X_train[list(FEATURE_COLUMNS)], residual)
    return TrendAwareModel(trend_model=trend_model, residual_rf=residual_rf)


def tree_prediction_band(
    model: RandomForestRegressor, X: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-tree predictions -> mean and 10th/90th percentiles."""
    X_values = X[list(FEATURE_COLUMNS)].to_numpy()
    matrix = np.column_stack([est.predict(X_values) for est in model.estimators_])
    mean = matrix.mean(axis=1)
    p10 = np.percentile(matrix, 10, axis=1)
    p90 = np.percentile(matrix, 90, axis=1)
    return mean, p10, p90


def compute_mse_mape(
    y_true: np.ndarray | pd.Series, y_pred: np.ndarray | pd.Series
) -> tuple[float, float]:
    """MSE in USD² and MAPE in percent."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mse = float(mean_squared_error(y_true_arr, y_pred_arr))
    mape = float(np.mean(np.abs(y_true_arr - y_pred_arr) / y_true_arr) * 100.0)
    return mse, mape


def compute_psi(
    y_train: np.ndarray | pd.Series, y_test: np.ndarray | pd.Series
) -> tuple[float, str]:
    """PSI on target distribution: train deciles, same edges on test."""
    y_train_arr = np.asarray(y_train, dtype=float)
    y_test_arr = np.asarray(y_test, dtype=float)
    edges = np.unique(np.quantile(y_train_arr, np.linspace(0.0, 1.0, 11)))
    if len(edges) < 2:
        raise ValueError("compute_psi: train target has insufficient variation for bins")

    expected_counts = np.histogram(y_train_arr, bins=edges)[0].astype(float)
    actual_counts = np.histogram(y_test_arr, bins=edges)[0].astype(float)
    expected = expected_counts / expected_counts.sum()
    actual = actual_counts / actual_counts.sum()

    floor = 1e-6
    expected = np.clip(expected, floor, None)
    actual = np.clip(actual, floor, None)
    expected = expected / expected.sum()
    actual = actual / actual.sum()

    psi = float(np.sum((actual - expected) * np.log(actual / expected)))
    if psi < 0.1:
        band = "stable (<0.1)"
    elif psi <= 0.25:
        band = "moderate (0.1-0.25)"
    else:
        band = "significant (>0.25 -> retrain)"
    return psi, band


def compute_gini(
    y_true: np.ndarray | pd.Series, y_score: np.ndarray | pd.Series
) -> float:
    """Gini = 2·AUC − 1; labels = above TEST-set median revenue."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_score_arr = np.asarray(y_score, dtype=float)
    median = float(np.median(y_true_arr))
    labels = (y_true_arr > median).astype(int)
    if labels.min() == labels.max():
        raise ValueError("compute_gini: degenerate labels (single class after median split)")
    auc = float(roc_auc_score(labels, y_score_arr))
    return 2.0 * auc - 1.0


def compute_k2(residuals: np.ndarray | pd.Series) -> tuple[float, float]:
    """D'Agostino's K² normality test on residuals."""
    result = stats.normaltest(np.asarray(residuals, dtype=float))
    return float(result.statistic), float(result.pvalue)


def feature_importance_table(model: RandomForestRegressor) -> dict[str, float]:
    """Map FEATURE_COLUMNS to RandomForest feature_importances_."""
    return {
        name: float(importance)
        for name, importance in zip(
            FEATURE_COLUMNS, model.feature_importances_, strict=True
        )
    }


def plot_test_forecast(
    months: pd.Series,
    y_actual: np.ndarray | pd.Series,
    y_naive: np.ndarray | pd.Series,
    y_trend_aware: np.ndarray | pd.Series,
    p10: np.ndarray,
    p90: np.ndarray,
    chart_path: Path,
) -> None:
    """Save actual vs naive RF vs trend-aware RF with p10–p90 band (test months)."""
    import matplotlib.pyplot as plt  # lazy: keep module import headless-CI safe

    chart_path.parent.mkdir(parents=True, exist_ok=True)
    x = pd.to_datetime(months)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, p10, p90, alpha=0.25, label="Naive RF p10–p90", color="#6b8cae")
    ax.plot(x, y_actual, label="Actual", color="#1a1a1a", linewidth=2)
    ax.plot(x, y_naive, label="Naive RF (graded)", color="#c45c26", linewidth=1.5)
    ax.plot(
        x,
        y_trend_aware,
        label="Trend-aware RF (productionization)",
        color="#2f6f4e",
        linewidth=1.5,
        linestyle="--",
    )
    ax.set_title("Consolidated revenue — test years 2024–2025")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (USD)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(chart_path, dpi=120)
    plt.close(fig)


def run_forecast(data_path: Path, chart_path: Path) -> dict[str, Any]:
    """Train graded + productionization models; metrics on TEST only; write chart."""
    df = load_sales(data_path)
    train_df, test_df = chronological_split(df)

    X_all, y_all = build_features(df)
    train_idx = df.index[pd.to_datetime(df["month"]).dt.year.isin(TRAIN_YEARS)]
    test_idx = df.index[pd.to_datetime(df["month"]).dt.year.isin(TEST_YEARS)]

    # Prefer split frames so feature trend is recomputed consistently per full series
    X_train = X_all.loc[train_idx].reset_index(drop=True)
    y_train = y_all.loc[train_idx].reset_index(drop=True)
    X_test = X_all.loc[test_idx].reset_index(drop=True)
    y_test = y_all.loc[test_idx].reset_index(drop=True)
    test_months = test_df["month"].reset_index(drop=True)

    naive = fit_naive_rf(X_train, y_train)
    trend_aware = fit_trend_aware_rf(X_train, y_train)

    y_naive = naive.predict(X_test[list(FEATURE_COLUMNS)])
    y_trend = trend_aware.predict(X_test)
    _, p10, p90 = tree_prediction_band(naive, X_test)

    mse, mape = compute_mse_mape(y_test, y_naive)
    psi, psi_band = compute_psi(y_train, y_test)
    gini = compute_gini(y_test, y_naive)
    residuals = np.asarray(y_test, dtype=float) - np.asarray(y_naive, dtype=float)
    mean_residual_usd = float(residuals.mean())
    k2_stat, k2_p = compute_k2(residuals)
    importances = feature_importance_table(naive)

    plot_test_forecast(
        months=test_months,
        y_actual=y_test,
        y_naive=y_naive,
        y_trend_aware=y_trend,
        p10=p10,
        p90=p90,
        chart_path=chart_path,
    )

    return {
        "mse": mse,
        "mape": mape,
        "mean_residual_usd": mean_residual_usd,
        "psi": psi,
        "psi_band": psi_band,
        "gini": gini,
        "k2_stat": k2_stat,
        "k2_p": k2_p,
        "feature_importances": importances,
        "chart_path": str(chart_path),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_max_revenue": float(y_train.max()),
        "test_max_revenue": float(y_test.max()),
    }
