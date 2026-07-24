# Pipelines tests

Pytest suite for weekly location-performance ETL helpers, job runner coordination, nightly export, and CLI wrappers under `data/pipelines/`.

## Testing

```powershell
uv run --directory data --python 3.13 pytest
```

Expect **32** passed.

The command uses the `data/` uv project because that environment owns the pipeline dependencies; `data/pyproject.toml` sets `testpaths` to `../tests/pipelines`.
