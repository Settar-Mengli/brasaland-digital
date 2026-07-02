# Brasaland Inventory API

PostgreSQL-backed inventory service for Brasaland Operations (ingredients, stock movements, orders).

## Setup

Run commands from `services/inventory/`:

```powershell
uv sync
uv run pytest
uv run uvicorn app:app --port 8012
```

`requirements.txt` is a generated pip-compat export (`uv export --no-hashes -o requirements.txt`).
