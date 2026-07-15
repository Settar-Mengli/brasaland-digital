# syntax=docker/dockerfile:1

# Dedicated reporting image: needs data/pipelines (generic services/Dockerfile does not COPY data/).

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY data/ data/
COPY services/reporting/ services/reporting/

WORKDIR /app/services/reporting

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/services/reporting

COPY --from=builder /app/data /app/data
COPY --from=builder /app/services/reporting /app/services/reporting

ENV VIRTUAL_ENV="/app/services/reporting/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"
ENV PYTHONPATH="/app/data"

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
