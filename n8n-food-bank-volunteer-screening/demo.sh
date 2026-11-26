#!/usr/bin/env bash
# Post every sign-up in data/signups.json to the webhook and print the reply.
set -euo pipefail
cd "$(dirname "$0")"
WEBHOOK="${WEBHOOK:-http://localhost:${N8N_PORT:-5678}/webhook/volunteer-signup}"

python3 -c "import json; [print(json.dumps(s)) for s in json.load(open('data/signups.json'))]" | while read -r signup; do
  name=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['name'])" "$signup")
  echo "── $name"
  for attempt in $(seq 1 15); do
    if OUT=$(curl -sf -X POST "$WEBHOOK" -H 'Content-Type: application/json' -d "$signup"); then
      echo "$OUT" | python3 -m json.tool; echo; continue 2
    fi
    sleep 2   # the webhook registers a few seconds after activation
  done
  echo "webhook did not answer at $WEBHOOK; did ./setup.sh finish?" >&2; exit 1
done
