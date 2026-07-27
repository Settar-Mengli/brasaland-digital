# Sales forecast evaluation report

Graded model: `RandomForestRegressor(random_state=42)` via `fit_naive_rf` on time-derived features only (`trend`, `month_sin`, `month_cos`, `year`). Produced by:

```powershell
uv run --directory data --python 3.13 python ../scripts/evaluate_sales_forecast.py
```

**Labels:** **train** = 2016–2023 fit set (96 rows); **validation** = in-train `TimeSeriesSplit` folds (train years only); **test** = 2024–2025 chronological holdout (24 rows). CV and the learning curve never include 2024–2025.

Chart: [`learning_curve.png`](learning_curve.png)

---

## Holdout MAE / RMSE (train vs test)

| Set | MAE (USD) | RMSE (USD) |
| --- | ---: | ---: |
| Train (2016–2023) | 11292.2244 | 14780.6897 |
| Test (2024–2025 holdout) | 47059.8157 | 59043.0049 |

Train max revenue: **889619.26** USD. Test max revenue: **994075.53** USD.

---

## Temporal CV (validation folds, train years only)

`TimeSeriesSplit(n_splits=5)` on the train slice only. Features built once on the full series then sliced (test `trend` continues 96..119); folds never rebuild features.

| Metric | Fold values | mean ± std (USD) |
| --- | --- | ---: |
| MAE | 18603.404, 39899.5513, 36790.4776, 36119.379, 58205.0805 | 37923.5785 ± 12594.0620 |
| RMSE | 25846.7905, 49802.3496, 46143.6427, 42043.2721, 67094.4276 | 46186.0965 ± 13274.6960 |

---

## Metric choice

**RMSE is primary**; MAE is reported beside it.

Large single-month misses (for example the December +20–30% spike in CONTEXT) cost more in absolute dollars than many small misses of the same total — RMSE up-weights those spikes and aligns with CONTEXT’s required MSE (RMSE = √MSE). This magnitude argument is **derived** from CONTEXT §1 (Felipe’s purchasing / Lucía’s volume planning) plus the documented seasonality pattern — **not** a CONTEXT-stated ranking of over-forecast vs under-forecast cost.

RMSE is **symmetric**: it does not encode whether under-forecast (stockout) hurts more than over-forecast (waste). Directional under-forecast risk is carried by the signed / mean residual from the train deliverable, not by RMSE alone.

---

## Diagnosis

Diagnosis: the model shows **OVERFITTING**. By the learning-curve criterion, a wide and persistent gap between low training error (MAE ~11.3k) and substantially higher validation error (MAE ~37.9k across the TimeSeriesSplit folds) that does not close as training size grows is the signature of overfitting — a default Random Forest fits the 2016-2023 window far more tightly than it generalizes to held-out months.

The gap is not primarily noise-memorization variance, however: a large, systematic component is the tree-ensemble trend-extrapolation ceiling. On the 2024-2025 holdout the actuals (max ~994k) exceed the training maximum (~890k), and no Random Forest predicts above its training leaves, so the graded model under-forecasts the rising test years by construction. In-sample temporal CV shows fit quality WITHIN 2016-2023; the holdout is what exposes the ceiling — CV alone does not prove it.

---

## Corrective action

**Detrend** for productionization: fit a linear trend on train, Random Forest on the seasonal residual, and re-add trend at predict time — the in-repo path is `TrendAwareModel` / `fit_trend_aware_rf` in `data/pipelines/sales_forecast.py`. That analysis is additive and **does not replace** the graded naive RF for the course grade. Do **not** “add regularization” to the graded forest as the fix for this ceiling.
