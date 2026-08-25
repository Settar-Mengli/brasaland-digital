# syntax=docker/dockerfile:1

# Production backoffice only. Does not use uis/start.sh (three next dev servers).

FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/operations-toolkit apps/operations-toolkit
COPY uis uis

RUN npm ci

FROM node:20-alpine AS build

WORKDIR /app

COPY --from=deps /app /app

ENV AUTH_API_ORIGIN=http://auth:8002
ENV RFP_API_ORIGIN=http://rfp:8017
ENV NEXT_PUBLIC_SLICE_NAV=1

RUN npm run build --workspace @brasaland/backoffice

FROM node:20-alpine AS runtime

WORKDIR /app

COPY --from=build /app /app

RUN chown -R node:node /app

ENV AUTH_API_ORIGIN=http://auth:8002
ENV RFP_API_ORIGIN=http://rfp:8017
ENV NEXT_PUBLIC_SLICE_NAV=1
ENV PORT=3003

USER node

EXPOSE 3003

CMD ["npm", "exec", "--workspace=@brasaland/backoffice", "--", "next", "start", "-p", "3003"]
