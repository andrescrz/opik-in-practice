# n8n-food-bank-volunteer-screening

**Trace every n8n workflow run in Opik without adding a single node.**

![n8n](https://img.shields.io/badge/n8n-2.41.7-EA4B71) ![tracing](https://img.shields.io/badge/tracing-OpenTelemetry-blue) ![code changes](https://img.shields.io/badge/workflow%20changes-0-brightgreen)

Riverbend Community Pantry, a fictional food bank, takes volunteer sign-ups through a web form. An n8n workflow
checks the hard rules (minimum ages, driver's licence, background check for the kids' program), asks gpt-4o-mini
to read the rest, and either books the volunteer or queues them for the coordinator.

When a volunteer later asks "why did I get sent to the front desk?", the coordinator needs to see what the
workflow actually did for that one submission: which rule fired, what the model was told, what it answered,
and which branch the IF node took. n8n keeps execution logs, but they live inside n8n and disappear when the
instance is rebuilt. Here every run lands in Opik as a trace, through a lifecycle hook baked into the n8n image.
The workflow JSON has no tracing nodes and no code for it.

## What you'll build

- `workflow/volunteer-screening.json`: Sign-up form (webhook), then Check shift rules (code), then Screen motivation (OpenAI, gpt-4o-mini), then Needs a coordinator? (IF), then Queue for coordinator or Ready to schedule (set), then Reply to form.
- An n8n image with [`n8n-observability`](https://www.npmjs.com/package/n8n-observability) loaded through `EXTERNAL_HOOK_FILES`. It exports one OpenTelemetry span per workflow run and one per node, and Opik ingests them on its OTLP endpoint.
- `setup.sh`, which needs no browser. It starts a fresh n8n, claims the instance, mints an API key, creates the OpenAI credential from your environment, then imports and activates the workflow through n8n's REST API.
- `demo.sh`, which posts the four fictional sign-ups in `data/signups.json`.

## See it in Opik

Open the **n8n-food-bank-volunteer-screening** project. One `./demo.sh` run gives **4 traces**, all named
**Volunteer screening**, one per sign-up.

Open any trace and you get **7 spans**: the root `Volunteer screening` span plus one per node that ran. That is
Sign-up form, Check shift rules, Screen motivation (gpt-4o-mini), Needs a coordinator?, one of the two Set nodes,
and Reply to form. Only the branch that actually ran shows up, so the tree itself tells you how the IF node decided.

What to click:

- **Check shift rules**: the span input holds the node's code (`n8n.node.parameters.jsCode`) and its output (`n8n.node.output`). For Jonah Whitaker, 19 and asking to drive deliveries, the output carries `hard_blockers: ["must be 21+ for delivery_driver"]`.
- **Screen motivation (gpt-4o-mini)**: the span carries the full system and user prompt (`n8n.node.parameters.messages.*`), plus the model's reply as `n8n.node.output.chat_messages`. On our run that reply was `decision: redirect, suggested_role: pantry_front_desk` for Jonah, and `decision: interview` for Ollie Brandt, who mentioned court-ordered service hours.
- **Reply to form**: the final JSON the volunteer's browser received.

If a node throws, its span and the root span both carry the error, with the message and stack. That is how we
found the credential problem described under Gotchas.

## Run it yourself

You need Docker, `curl`, `python3`, an OpenAI key and an Opik instance. A local self-hosted Opik on
`http://localhost:5173` works with no API key. For Opik Cloud, set `OPIK_URL_OVERRIDE` and `OPIK_API_KEY`.

1. Put `OPENAI_API_KEY` (and, for Opik Cloud, `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` / `OPIK_API_KEY`) in the repo-root `.env` or export them. See `.env.example`.
2. `./setup.sh`: builds the image and prints the n8n URL and login once the workflow is active.
3. `./demo.sh`: sends the four sign-ups and prints each reply.
4. Open the **n8n-food-bank-volunteer-screening** project in Opik.
5. `./teardown.sh` when you're done. It removes the container and its volume.

The n8n UI is on `http://localhost:5678` (login `coordinator@riverbend.example` / `Riverbend-demo-1`, a
local-only demo account). Set `N8N_PORT` to move it.

Offline tests (no n8n, no Opik, no keys): `node --test`. They check the exported workflow's node chain and run
the **Check shift rules** code against the sample sign-ups.

## Poke around

- Carmen Delgado wants the kids' snack program and has both certificates. The prompt says kid-facing roles need an interview first. Across our runs the model answered both `approve` and `interview` for her. Run `./demo.sh` a few times and compare her **Screen motivation** spans side by side: the prompt is identical, and only the reply moves.
- Change Jonah's age to 22 in `data/signups.json` and re-run. **Check shift rules** now reports no blockers, so the age-based redirect is gone and the model decides on its own. See which branch the trace takes.
- Rename a node in the n8n editor and run a sign-up through it. The span name follows the node name, so name nodes for the people reading traces.
- Set `N8N_OTEL_NODE_EXCLUDE` (comma-separated node names or node types) in `docker-compose.yml` to keep noisy nodes out of the trace. `N8N_OTEL_NODE_INCLUDE` does the opposite.

## Gotchas we hit

- **`Credential with ID "…" does not exist for type "openAiApi"` on every run after the first.** Our first `setup.sh` deleted the old workflow and credential through the API and imported fresh copies. The webhook stayed bound to the deleted copy, so every sign-up failed at the OpenAI node with HTTP 500. In Opik that showed up as traces that stop at **Screen motivation** with the error attached. Fix: `setup.sh` now starts from an empty volume (`docker compose down -v` before `up`), so every setup is a clean instance.
- **The OpenAI node shows no tokens or cost.** `n8n-observability` tags the node `n8n.span.type=llm` and records the prompt and reply, but the n8n OpenAI node does not hand token usage to the hook. Opik therefore stores it as a general span with no usage. For per-call cost, trace the model call from code instead (see the other examples in this repo).
- **Nothing arrives from inside Docker.** `localhost` inside the n8n container is the container itself. `setup.sh` rewrites `localhost` in `OPIK_URL_OVERRIDE` to `host.docker.internal`, and `docker-compose.yml` maps that name on Linux too (`host-gateway`).

## How it's put together

- `workflow/volunteer-screening.json`: the workflow. `__OPENAI_CREDENTIAL_ID__` is filled in at import time, so no key or credential id is ever committed.
- `Dockerfile`: n8n 2.41.7 plus `n8n-observability` 1.0.3, wired in with `EXTERNAL_HOOK_FILES`. This is the whole Opik integration.
- `docker-compose.yml`: the OTLP endpoint and headers (`Comet-Workspace`, `projectName`) come from `setup.sh`.
- `setup.sh`: headless install and import through n8n's REST and public APIs.
- `demo.sh`: posts `data/signups.json` to the webhook.
- `teardown.sh`: removes the container and volume.
- `data/signups.json`: four fictional volunteers.
- `tests/workflow.test.mjs`: offline checks on the workflow JSON and its shift-rules code.

---

*built with Opik · inspired by Opik's examples and documentation*
