FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/operations-toolkit apps/operations-toolkit
COPY uis uis

RUN npm ci

EXPOSE 3002 3003 3004

ENV WATCHPACK_POLLING=true

CMD ["sh", "uis/start.sh"]
