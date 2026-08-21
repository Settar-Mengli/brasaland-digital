# syntax=docker/dockerfile:1

ARG SERVICE=__MISSING_SERVICE__

FROM python:3.13-slim AS builder

ARG SERVICE

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY packages/ packages/
COPY services/${SERVICE}/ services/${SERVICE}/

WORKDIR /app/services/${SERVICE}

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

ARG SERVICE

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/services/${SERVICE}

COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/services/${SERVICE} /app/services/${SERVICE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --home-dir /home/app app \
    && mkdir -p /app/services/${SERVICE}/data \
    && chown -R app:app /app

ENV VIRTUAL_ENV="/app/services/${SERVICE}/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"

USER app

CMD ["python", "-c", "print('Override CMD with uvicorn via compose')"]
