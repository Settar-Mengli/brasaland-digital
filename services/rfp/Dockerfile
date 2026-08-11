# syntax=docker/dockerfile:1

# Dedicated RFP image: needs data/pipelines + packages/auth-verify
# (generic services/Dockerfile does not COPY data/).

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY packages/ packages/
COPY data/ data/
COPY services/rfp/ services/rfp/

WORKDIR /app/services/rfp

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/services/rfp

COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/data /app/data
COPY --from=builder /app/services/rfp /app/services/rfp

ENV VIRTUAL_ENV="/app/services/rfp/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"
ENV PYTHONPATH="/app/data"

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
