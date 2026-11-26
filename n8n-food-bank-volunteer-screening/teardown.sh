#!/usr/bin/env bash
# Stop n8n and delete its volume (workflows, credentials, owner account).
set -euo pipefail
cd "$(dirname "$0")"
docker compose down -v
