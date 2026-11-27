# dify-gym-assistant

**A no-code Dify chat app, traced in Opik by flipping a setting.**

![Dify](https://img.shields.io/badge/Dify-1.17.1-1C64F2) ![model](https://img.shields.io/badge/model-gpt--4o--mini-412991) ![app code](https://img.shields.io/badge/app%20code-0%20lines-brightgreen)

Ironbark Fitness Co-op is a fictional member-owned gym. Its front-desk assistant was built in Dify, with no
application code at all: a system prompt holding the gym's facts (prices, freeze rules, guest passes, the weekly
class schedule) and gpt-4o-mini behind it. Members reach it from a website chat widget.

Apps like this are where observability usually stops. There is no function to decorate and no client to wrap.
Dify has a built-in Opik integration, though. Give it four fields (URL, workspace, project, API key), switch it
on, and every member message lands in Opik with the full prompt Dify assembled, the answer and the token counts.
This example does that headlessly, so the whole stack comes up from a script.

## What you'll build

- A self-hosted Dify 1.17.1 stack from Dify's own docker-compose files (vendored in `dify-docker/`).
- The **Ironbark Gym Assistant** chat app, imported from `app/ironbark-gym-assistant.yml`, Dify's export format. The app is a committed file, not something clicked together.
- `dify_setup.py`, which does what you would otherwise click through: admin account, OpenAI plugin and key, app import, then the Opik part (save the trace config, switch tracing on) and a service API key.
- `demo.py`, which plays a website widget: two members, each in their own conversation, five messages in all.

## See it in Opik

Open the **dify-gym-assistant** project after `python3 demo.py`. One run gave us **7 traces**:

- **5 `message` traces**, one per member message. Each holds one `llm` span whose input is the exact message list Dify sent: the system prompt with every Ironbark fact in it, the earlier turns, then the new question. On our run prompt tokens went 641, 703, 749 across Ana's three turns, and 635 then 680 across Raj's two. That is the conversation history being re-sent each turn, and you can see it without instrumenting anything.
- **2 `generate_conversation_name` traces**, one per conversation. Dify makes an extra LLM call to title each chat. You never asked for it, but platform-level tracing shows it.

Switch to the **Threads** tab. Dify passes its conversation id as the Opik thread id, so you get two threads: Ana
with 4 traces (3 messages plus the title call) and Raj with 3.

Now the reason you'd want this. Open Ana's first `message` trace ("I'm on the off-peak plan. Can I come to the
Monday evening spin class?"). The answer says the class isn't included and costs $12. Expand the system prompt
in the `llm` span input: off-peak members can only come in **weekdays 9:00-16:00**, so an 18:30 class is out of
reach whatever she pays. The model had the fact and missed it, in both of our runs. Without the trace you'd be
guessing whether the handbook text, the prompt or the model was wrong. With it, the answer takes one click.

Raj's second message ("My knee hurts after squats…") shows the other side: the prompt's "no medical advice" rule
working, with a polite redirect to the front desk.

## Run it yourself

You need Docker with about 15 GB of free image space (Dify pulls roughly ten images), Python 3, an OpenAI key,
and an Opik instance. A local self-hosted Opik on `http://localhost:5173` needs no API key.

1. Put `OPENAI_API_KEY` (and, for Opik Cloud, `OPIK_URL_OVERRIDE`, `OPIK_WORKSPACE`, `OPIK_API_KEY`) in the repo-root `.env` or export them. See `.env.example`.
2. `./setup.sh`: starts Dify on `http://localhost:8090` and configures everything. The first run takes a few minutes.
3. `python3 demo.py`: sends the five messages and prints answers and token counts.
4. Open the **dify-gym-assistant** project in Opik. Dify sends traces from a background worker, so give it a few seconds.
5. `./teardown.sh` removes the containers, volumes and local state.

The Dify UI login is `desk@ironbark.example` / `IronbarkDesk2026`, a local-only demo account. Set `DIFY_PORT` to
move it off 8090.

Offline tests (no Dify, no Opik, no keys): `python3 -m unittest discover tests`. They check the Opik settings
`dify_setup.py` saves, including the `localhost` rewrite, and that re-running updates rather than duplicates.

## Poke around

- Add "18:30 is outside off-peak hours" style guidance to the prompt in the Dify UI (or the DSL) and re-run `demo.py`. Compare Ana's two first-turn traces side by side.
- In the Dify UI, open the app's **Monitoring** panel: the Opik settings `dify_setup.py` wrote are there, and you can switch tracing off and on without touching code.
- Ask a long multi-turn conversation through `demo.py` and watch prompt tokens climb in the Threads view.
- Turn the app into a Dify chatflow (workflow) app. Dify then reports each workflow node as its own span.

## Gotchas we hit

- **`400 tracing_config_verification_failed` when saving the Opik settings.** Dify checks the config by calling Opik from inside its containers, where `localhost` is the container itself. With `http://localhost:5173/api/` the save fails. `dify_setup.py` rewrites `localhost` to `host.docker.internal` before saving.
- **Token counts but no cost.** Dify's Opik integration puts the model name in span metadata (`ls_model_name: gpt-4o-mini`, `ls_provider: langgenius/openai/openai`), not in the span's model field, so Opik has no model to price and the cost column stays empty. Usage is there; multiply it yourself or trace the call from code if you need dollars.
- **Saving the config doesn't turn tracing on.** The trace config and the on/off switch are separate calls (`POST /apps/{id}/trace-config`, then `POST /apps/{id}/trace` with `enabled: true`). Skip the second and nothing is sent.
- **Docker runs out of room.** On a machine already running other compose stacks, Dify's first `up` failed twice for us: `no space left on device` while pulling, then `all predefined address pools have been fully subnetted` (Dify creates four networks). `docker builder prune` / `docker image prune` and `docker network prune` freed enough for it to start.

## How it's put together

- `app/ironbark-gym-assistant.yml`: the Dify app (system prompt with the gym facts, gpt-4o-mini, temperature 0.2).
- `dify_setup.py`: headless configuration through Dify's console API, standard library only. `opik_tracing()` is the whole Opik integration.
- `setup.sh`: creates `dify-docker/.env` from Dify's template (port 8090), starts the stack and runs `dify_setup.py`.
- `demo.py`: two member conversations through Dify's service API (`/v1/chat-messages`).
- `teardown.sh`: stops the stack and deletes its data.
- `docker-compose.localhost.yaml`: layered over Dify's compose file so its ports listen on this machine only, never on your network.
- `tests/test_dify_setup.py`: offline tests for `dify_setup.py` against a fake console.
- `dify-docker/`: Dify's upstream docker-compose files for release 1.17.1.

---

*built with Opik · inspired by Opik's examples and documentation*
