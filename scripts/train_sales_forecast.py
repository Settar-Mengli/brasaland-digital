"""Train graded Random Forest sales forecast on consolidated monthly revenue.

Invocation (authoritative)::

    uv run --directory data --python 3.13 python ../scripts/train_sales_forecast.py

Prints TEST-set MSE(+MAPE), PSI, Gini, and K2; writes the prediction chart under
data/eval/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
if str(DATA_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ROOT))

from pipelines.sales_forecast import run_forecast  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Train RandomForestRegressor(random_state=42) on brasaland_sales.csv; "
            "evaluate on 2024–2025 held-out months; write eval chart."
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
        default=REPO_ROOT / "data" / "eval" / "sales_forecast_test.png",
        help="Output PNG path (default: data/eval/sales_forecast_test.png).",
    )
    args = parser.parse_args()

    summary = run_forecast(args.data.resolve(), args.chart.resolve())

    print("=== Graded model: naive RandomForestRegressor(random_state=42) ===")
    print(f"Train rows: {summary['train_rows']}  Test rows: {summary['test_rows']}")
    print(
        f"Train max revenue: {summary['train_max_revenue']:.2f}  "
        f"Test max revenue: {summary['test_max_revenue']:.2f}"
    )
    print("--- TEST-set metrics ---")
    print(f"MSE (USD^2): {summary['mse']:.4f}")
    print(f"MAPE (%):    {summary['mape']:.4f}")
    mean_res = float(summary["mean_residual_usd"])
    print(
        f"Mean residual (bias): {mean_res:+,.2f} USD  "
        "(positive = model under-predicts)"
    )
    print(f"PSI:         {summary['psi']:.6f}  band={summary['psi_band']}")
    print(
        "PSI note: high PSI is EXPECTED here - volumes outgrew the training envelope."
    )
    print(f"Gini:        {summary['gini']:.6f}")
    print(f"K2 stat:     {summary['k2_stat']:.6f}")
    print(f"K2 p-value:  {summary['k2_p']:.6g}")
    print("--- Feature importances (graded RF) ---")
    for name, value in summary["feature_importances"].items():
        print(f"  {name}: {value:.6f}")
    print("--- Productionization ---")
    print(
        "Trend-aware RF (linear trend + RF residual) plotted beside naive RF; "
        "does not replace the graded model."
    )
    print(f"Chart: {summary['chart_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
