#!/usr/bin/env bash
# Headless setup: start n8n, claim the instance, mint an API key, create the
# OpenAI credential from $OPENAI_API_KEY, then import and activate the workflow.
set -euo pipefail
cd "$(dirname "$0")"

# Load the repo-root .env without overriding anything already exported.
if [ -f ../.env ]; then
  while IFS='=' read -r k v; do
    [[ -z "$k" || "$k" == \#* ]] && continue
    [ -z "${!k:-}" ] && export "$k=$v"
  done < ../.env
fi
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell env or repo-root .env)}"

export N8N_PORT="${N8N_PORT:-5678}"
N8N_URL="http://localhost:${N8N_PORT}"
OWNER_EMAIL="coordinator@riverbend.example"
OWNER_PASSWORD="Riverbend-demo-1"
BROWSER_ID="setup-script"

json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1)"; }

echo "==> Starting n8n on ${N8N_URL}"
docker compose up -d --build

echo -n "==> Waiting for n8n"
for _ in $(seq 1 90); do
  curl -sf "$N8N_URL/healthz/readiness" >/dev/null 2>&1 && { echo " up"; break; }
  echo -n "."; sleep 2
done
curl -sf "$N8N_URL/healthz/readiness" >/dev/null || { echo "n8n did not come up"; exit 1; }

COOKIES="$(mktemp)"; trap 'rm -f "$COOKIES"' EXIT
rest() { curl -sf -b "$COOKIES" -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" -X "$1" "$N8N_URL/rest$2" ${3:+-d "$3"}; }

echo "==> Claiming the instance (or logging in if already claimed)"
AUTHED=""
for _ in $(seq 1 15); do
  if rest POST /owner/setup "{\"email\":\"$OWNER_EMAIL\",\"firstName\":\"Pantry\",\"lastName\":\"Coordinator\",\"password\":\"$OWNER_PASSWORD\"}" >/dev/null 2>&1 \
     || rest POST /login "{\"emailOrLdapLoginId\":\"$OWNER_EMAIL\",\"password\":\"$OWNER_PASSWORD\"}" >/dev/null 2>&1; then
    AUTHED=yes; break
  fi
  sleep 2
done
[ -n "$AUTHED" ] || { echo "could not authenticate against n8n"; exit 1; }

echo "==> Minting an API key"
API_KEY=$(rest POST /api-keys '{"label":"setup-'"$(date +%s)"'","expiresAt":null,"scopes":["workflow:create","workflow:read","workflow:delete","workflow:list","workflow:activate","credential:create","credential:delete"]}' | json "['data']['rawApiKey']")
api() { curl -sf -X "$1" "$N8N_URL/api/v1$2" -H "X-N8N-API-KEY: $API_KEY" -H 'Content-Type: application/json' ${3:+-d "$3"}; }

if [ -f .n8n-credential-id ]; then
  api DELETE "/credentials/$(cat .n8n-credential-id)" >/dev/null 2>&1 || true
fi
echo "==> Creating the OpenAI credential (from the environment, never from a file)"
CRED_ID=$(api POST /credentials "{\"name\":\"OpenAI (volunteer screening)\",\"type\":\"openAiApi\",\"data\":{\"apiKey\":\"$OPENAI_API_KEY\"}}" | json "['id']")
echo "$CRED_ID" > .n8n-credential-id

echo "==> Replacing any previous copy of the workflow"
api GET "/workflows?name=Volunteer%20screening" \
  | python3 -c "import json,sys; [print(w['id']) for w in json.load(sys.stdin).get('data',[])]" \
  | while read -r wid; do api DELETE "/workflows/$wid" >/dev/null; done
WF_BODY=$(sed "s/__OPENAI_CREDENTIAL_ID__/$CRED_ID/" workflow/volunteer-screening.json)
WF_ID=$(api POST /workflows "$WF_BODY" | json "['id']")
api POST "/workflows/$WF_ID/activate" >/dev/null

echo
echo "n8n UI:  $N8N_URL  (login: $OWNER_EMAIL / $OWNER_PASSWORD)"
echo "Webhook: $N8N_URL/webhook/volunteer-signup"
echo "Next:    ./demo.sh"
