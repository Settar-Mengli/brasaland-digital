# syntax=docker/dockerfile:1

# Dedicated reporting image: needs data/pipelines (generic services/Dockerfile does not COPY data/).

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY packages/ packages/
COPY data/ data/
COPY services/reporting/ services/reporting/

WORKDIR /app/services/reporting

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/services/reporting

COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/data /app/data
COPY --from=builder /app/services/reporting /app/services/reporting

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --home-dir /home/app app \
    && chown -R app:app /app

ENV VIRTUAL_ENV="/app/services/reporting/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"
ENV PYTHONPATH="/app/data"

USER app

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
