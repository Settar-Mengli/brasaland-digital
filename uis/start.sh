#!/bin/sh

cleanup() {
  kill -TERM $(jobs -p) 2>/dev/null
  wait
}

trap cleanup TERM INT

npm run dev --workspace @brasaland/website &
npm run dev --workspace @brasaland/backoffice &
npm run dev --workspace @brasaland/incident-manager &

wait
