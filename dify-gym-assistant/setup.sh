#!/usr/bin/env bash
# Start a self-hosted Dify and configure the gym assistant headlessly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$HERE/dify-docker"
COMPOSE=(docker compose -f "$DOCKER_DIR/docker-compose.yaml" -f "$HERE/docker-compose.localhost.yaml" --project-directory "$DOCKER_DIR")

# Load the repo-root .env without overriding variables already exported.
if [ -f "$HERE/../.env" ]; then
  while IFS='=' read -r k v; do
    [[ -z "$k" || "$k" == \#* ]] && continue
    [ -z "${!k:-}" ] && export "$k=$v"
  done < "$HERE/../.env"
fi

DIFY_PORT="${DIFY_PORT:-8090}"

# dify-docker/.env comes from Dify's own template; we only pin the compose
# project name and move the ports off 80/443.
if [ ! -f "$DOCKER_DIR/.env" ]; then
  cp "$DOCKER_DIR/env.example" "$DOCKER_DIR/.env"
  cat >> "$DOCKER_DIR/.env" <<CONF

# --- ironbark gym assistant ---
COMPOSE_PROJECT_NAME=dify-gym-assistant
EXPOSE_NGINX_PORT=$DIFY_PORT
EXPOSE_NGINX_SSL_PORT=${DIFY_SSL_PORT:-8453}
CONF
fi

echo "Starting Dify (the first run pulls about ten images)..."
"${COMPOSE[@]}" up -d

DIFY_URL="http://localhost:$DIFY_PORT" python3 "$HERE/dify_setup.py"
echo "Dify UI: http://localhost:$DIFY_PORT  (login desk@ironbark.example / IronbarkDesk2026)"
