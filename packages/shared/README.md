# brasaland-shared

Pure incident field validation and lifecycle rules for Brasaland Python services (`brasaland_shared`). Zero runtime dependencies.

## Install (editable, from a consuming service)

Pip (`requirements.txt`):

```
-e ../../packages/shared
```

Uv (`pyproject.toml`):

```toml
dependencies = ["brasaland-shared"]

[tool.uv.sources]
brasaland-shared = { path = "../../packages/shared", editable = true }
```

## Testing

```powershell
cd packages/shared
uv run pytest
```

Expect **33** passed.

## requirements.txt

Generated for pip compatibility (runtime export only):

```powershell
uv export --no-hashes -o requirements.txt
```
