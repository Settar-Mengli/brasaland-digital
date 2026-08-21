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

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --home-dir /home/app app \
    && mkdir -p /app/checkpoint /app/data/raw \
    && chown -R app:app /app

ENV VIRTUAL_ENV="/app/services/rfp/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"
ENV PYTHONPATH="/app/data"

USER app

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
