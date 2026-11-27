#!/usr/bin/env bash
# Stop Dify and delete its databases and local state.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "$HERE/dify-docker/docker-compose.yaml" -f "$HERE/docker-compose.localhost.yaml" \
  --project-directory "$HERE/dify-docker" down -v
rm -rf "$HERE/dify-docker/volumes/app" "$HERE/dify-docker/volumes/db" "$HERE/dify-docker/volumes/redis" \
       "$HERE/dify-docker/volumes/weaviate" "$HERE/dify-docker/volumes/plugin_daemon" "$HERE/.dify-state.json"
