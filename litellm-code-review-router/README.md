# litellm-code-review-router

*Send the same code-review prompts to OpenAI and Anthropic, then read cost and latency per model side by side.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)

Choosing a model for a code-review assistant is mostly a cost-versus-speed question, and every provider reports usage differently. This app removes that friction: it reviews five small fictional patches with `gpt-4o-mini` and `claude-haiku-4-5`, routes both through LiteLLM, and lets Opik record the tokens, cost and latency of each call under one project.

## What you'll build

A small CLI split into three modules:

- a **router** (`router_app/router.py`) with one traced function, `route(model, messages)`, that works for any LiteLLM model string;
- a **reviewers** module that loads the patches in `data/patches.json` and builds the review prompt (one-line summary plus a risk rating);
- a **report** module that turns the calls into the comparison table printed at the end.

## See it in Opik

Open the `litellm-code-review-router` project. In one run the Traces tab holds 10 traces named `route_review` (5 patches x 2 models), and the Spans view holds 20 spans: 10 `general` spans from the traced function and 10 `llm` spans, one per completion, nested under their trace. Filter the spans by type `llm` and the model column splits into `gpt-4o-mini-2024-07-18` and `claude-haiku-4-5-20251001`, each with usage and a non-null estimated cost. Every llm span is also tagged with its short model name.

The numbers from that run, which match the table the CLI prints:

| Model | Reviews | Tokens | Cost (USD) | Mean latency |
|---|---|---|---|---|
| gpt-4o-mini | 5 | 1162 | 0.000296 | 1.45s |
| claude-haiku-4-5-20251001 | 5 | 1511 | 0.003179 | 1.50s |

Haiku cost roughly 10x more for these patches, partly through a higher per-token price and partly through longer answers, while latency was nearly identical. Sort the span table by estimated cost to see it directly.

## Run it yourself

1. `cp .env.example .env` and fill in `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` (a repo-root `.env` is also picked up). Point `OPIK_URL_OVERRIDE` at your Opik, or use Opik Cloud settings.
2. `uv sync`
3. `uv run main.py`
4. Open the project in Opik as described above.

Offline tests: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Add a third string to `MODELS` in `router_app/router.py` (for example a Gemini model) and re-run; nothing else changes.
- Add a patch to `data/patches.json`, such as one with an obvious bug, and compare how each model rates its risk.
- Change `SYSTEM` in `router_app/reviewers.py` to demand a full paragraph and watch the cost gap move.
- Delete the `current_span_data` line in `route()` and re-run to see the orphaned traces described below.

## Gotchas we hit

- **Symptom:** the `llm` spans show up as separate top-level traces, with the `route_review` traces left empty. **Cause:** LiteLLM's Opik callback does not know about the active `@opik.track` span. **Fix:** pass it in the call metadata: `metadata={"opik": {"current_span_data": get_current_span_data()}}` (`from opik.opik_context import get_current_span_data`).
- **Symptom:** `credit balance is too low` or auth errors even after you updated `.env`. **Cause:** `python-dotenv` does not override keys already exported in your shell, so stale `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` (or an `ANTHROPIC_BASE_URL` proxy) win. **Fix:** run with them unset: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u ANTHROPIC_BASE_URL uv run main.py`.
- **Symptom:** a `RuntimeError: no running event loop` / `periodic_flush was never awaited` warning at start-up. **Cause:** LiteLLM's Opik logger starts an async flusher in a plain script. **Effect:** harmless here; traces and costs still arrive, including for Haiku.

## How it's put together

- `main.py`: loads `.env`, sets the Opik project, installs the LiteLLM Opik callback, loops patches x models, prints the table and flushes.
- `router_app/router.py`: model list and the traced `route()` call.
- `router_app/reviewers.py`: patch loading and prompt building.
- `router_app/report.py`: per-model aggregation table.
- `data/patches.json`: five fictional patches.
- `tests/test_app.py`: offline tests for loading, the table, and a traced call with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
