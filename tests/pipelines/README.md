# Pipelines tests

Pytest suite for weekly location-performance ETL helpers, job runner coordination, nightly export, CLI wrappers under `data/pipelines/`, the sales-forecast chronological split (`test_sales_forecast_split.py`), temporal CV fold order (`test_regression_cv.py`), and M9 RFP intake graph/repository offline tests (`test_rfp_*.py`).

## Testing

```powershell
uv run --directory data --python 3.13 pytest
```

Expect **225** passed.

The command uses the `data/` uv project because that environment owns the pipeline dependencies; `data/pyproject.toml` sets `testpaths` to `../tests/pipelines`.
