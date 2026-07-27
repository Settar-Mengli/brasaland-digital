# Sales forecasting eval (graded deliverable)

Predict consolidated monthly `revenue_usd` with a chronological Random Forest.

Company context: [`../raw/CONTEXT-brasaland.en.md`](../raw/CONTEXT-brasaland.en.md)

## How to run

From the repo root (uses the `data/` uv project):

**Train (graded RF + forecast chart):**

```powershell
uv run --directory data --python 3.13 python ../scripts/train_sales_forecast.py
```

**Evaluate (holdout MAE/RMSE, temporal CV, learning curve):**

```powershell
uv run --directory data --python 3.13 python ../scripts/evaluate_sales_forecast.py
```

Input: [`data/raw/brasaland_sales.csv`](../raw/brasaland_sales.csv)  
Forecast chart: [`sales_forecast_test.png`](sales_forecast_test.png)  
Learning curve: [`learning_curve.png`](learning_curve.png)  
Evaluation report: [`evaluation_report.md`](evaluation_report.md)

## Model choice: Random Forest over XGBoost

Stakeholder is Finance / Mariana — the deliverable needs an **explainable number**, not a black-box accuracy contest. On this dataset the test years already exceed the training maximum (~994k vs ~889k USD). No tree ensemble extrapolates above its training leaves, so XGBoost’s usual accuracy edge is structurally neutralized here. Graded model: `RandomForestRegressor(random_state=42)`.

## Features (no leakage, no scaler)

Time-derived from `month` only: `trend`, `month_sin`, `month_cos`, `year`.

`covers_served` and `avg_ticket_usd` are **excluded** — same-month `covers × ticket ≈ revenue` to the dollar (target leakage).

**Null handling:** `load_sales` requires `month` and `revenue_usd` to be non-null and non-empty and raises a clear error if any fail. The syllabus dataset is clean; this is a **guard**, not a cleaner (no imputation or row-drop pipeline).

**Scaling:** no scaler. Random Forest splits are threshold-based and **scale-invariant**, so differing magnitudes (trend 0–119, sin/cos −1..1, year ~2016–2025) need no scaling. Scaling would matter for distance- or gradient-based models, not here.

## Split

Chronological, no shuffle: train 2016–2023 (96 rows), test 2024–2025 (24 rows). Metrics are computed on the **test set only**.

## Metrics (why MSE alone is insufficient)

| Metric | What it measures |
| --- | --- |
| **MSE (+ MAPE)** | Point accuracy in USD²; MAPE translates error for a business reader |
| **Mean residual** | Directional bias of errors (mean of `y_true - y_pred`); positive = under-prediction |
| **PSI** | Train↔test **target distribution** shift (train deciles, same edges on test). Bands: `<0.1` stable, `0.1–0.25` moderate, `>0.25` significant → retrain. **High PSI is EXPECTED here** — volumes outgrew the training envelope |
| **Gini** | Rank discrimination of good vs bad months (`2·AUC − 1`); labels = above/below the **test-set** median revenue (not train median) |
| **K2** | D’Agostino normality test on the test residuals' *shape* (`scipy.stats.normaltest`) — skewness/kurtosis, NOT bias. High p ⇒ residuals are well-shaped (no skew/heavy tails). Normal shape does not mean unbiased: directional under-prediction surfaces in MAPE and the mean residual, not in K2 |

Low MSE alone can hide distribution shift (PSI), weak ranking of strong vs weak months (Gini), and non-normal residual shape (K2) — and directional bias shows up only in MAPE and the mean residual. Finance needs all of them together.

> The observed Gini is low (~0.08) by design, not defect: because both `trend` and `year` exceed the training range, the RF predicts each calendar month identically across 2024 and 2025 — it is structurally blind to the year-over-year growth that drives the actual good/bad-month split. Low Gini is the extrapolation ceiling surfacing in a second metric, and is the core justification for the trend-aware variant below.

## Chart

`sales_forecast_test.png` shows 2024–2025 actual vs graded naive RF vs productionization trend-aware RF, with a shaded **p10–p90** band from per-tree predictions of the naive RF (prediction with its variability range, not a single number). The plotted naive-RF line is the ensemble mean (`model.predict`), and the shaded band is the 10th–90th percentile of the individual trees' predictions around that same mean — so the band is centered on the line by construction.

## Evaluation (MAE / RMSE + temporal CV)

[`scripts/evaluate_sales_forecast.py`](../../scripts/evaluate_sales_forecast.py) and [`pipelines/model_eval.py`](../pipelines/model_eval.py) evaluate the **graded** naive RF only (`fit_naive_rf`).

- **Train / test holdout:** MAE and RMSE on the 2016–2023 fit set and the 2024–2025 chronological **test** holdout.
- **Validation CV:** `TimeSeriesSplit` (≥5 folds) on the **train years only** — never includes 2024–2025. Features are built once on the full series then sliced (test `trend` continues 96..119); folds never rebuild features.
- **Learning curve:** [`learning_curve.png`](learning_curve.png) — train vs **validation** error with explicit `TimeSeriesSplit` (not sklearn’s default CV).
- **Report:** [`evaluation_report.md`](evaluation_report.md) — tables, metric rationale (RMSE primary), diagnosis separating in-train CV from the holdout extrapolation ceiling, and detrend corrective action via existing `TrendAwareModel`.

## Productionization analysis (additive — does not replace the graded RF)

1. **Trend-aware RF:** fit a linear trend on train, RF on the seasonal residual, re-add trend at predict time. Plotted on the same chart to show the naive RF’s extrapolation ceiling.
2. **Feature importance:** printed by the train script from the graded RF’s `feature_importances_`.
