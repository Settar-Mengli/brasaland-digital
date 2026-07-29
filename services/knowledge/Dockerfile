# syntax=docker/dockerfile:1

# Dedicated knowledge image: needs data/pipelines (generic services/Dockerfile does not COPY data/).
# Corpus markdown is compose-mounted (not COPYd) — see docker-compose knowledge volumes.

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY packages/ packages/
COPY data/ data/
COPY services/knowledge/ services/knowledge/

WORKDIR /app/services/knowledge

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/services/knowledge

COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/data /app/data
COPY --from=builder /app/services/knowledge /app/services/knowledge

ENV VIRTUAL_ENV="/app/services/knowledge/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"
ENV PYTHONPATH="/app/data"

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
