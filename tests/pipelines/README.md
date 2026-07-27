# Pipelines tests

Pytest suite for weekly location-performance ETL helpers, job runner coordination, nightly export, CLI wrappers under `data/pipelines/`, and the sales-forecast chronological split (`test_sales_forecast_split.py`).

## Testing

```powershell
uv run --directory data --python 3.13 pytest
```

Expect **33** passed.

The command uses the `data/` uv project because that environment owns the pipeline dependencies; `data/pyproject.toml` sets `testpaths` to `../tests/pipelines`.
