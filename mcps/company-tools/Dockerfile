# syntax=docker/dockerfile:1

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY packages/ packages/
COPY mcps/company-tools/ mcps/company-tools/

WORKDIR /app/mcps/company-tools

RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/mcps/company-tools

COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/mcps/company-tools /app/mcps/company-tools

ENV VIRTUAL_ENV="/app/mcps/company-tools/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:/bin:${PATH}"

CMD ["uv", "run", "company-tools-mcp"]
