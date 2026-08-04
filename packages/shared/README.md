# brasaland-shared

Pure incident field validation and lifecycle rules for Brasaland Python services (`brasaland_shared`). Zero runtime dependencies.

## Install (editable, from a consuming service)

Add to the service `pyproject.toml`:

```toml
dependencies = ["brasaland-shared"]

[tool.uv.sources]
brasaland-shared = { path = "../../packages/shared", editable = true }
```

Then sync from the consuming service:

```powershell
uv sync --python 3.13
```

## Testing

```powershell
cd packages/shared
uv sync --python 3.13
uv run pytest
```

Expect **33** passed.
