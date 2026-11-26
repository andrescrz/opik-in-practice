# openai-agents-insurance-claims

*A claims desk made of agents, where every handoff and every policy lookup is a span you can click.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB) ![openai-agents](https://img.shields.io/badge/openai--agents-0.22%2B-412991) ![opik](https://img.shields.io/badge/opik-2.3.5%2B-2f54eb)

When a claims assistant tells a customer "you're not covered", someone will eventually ask why. Was it the
triage agent sending a flood claim to the wrong specialist? The specialist skipping the coverage check? Or the
policy data really excluding flood? In a multi-agent app the final reply hides all of that. This example is a
small claims-intake desk for a fictional insurer, Larkspur Mutual, wired to Opik so each question has a visible
answer.

## What you'll build

Four `gpt-4o-mini` agents built with the OpenAI Agents SDK:

- **Claims Triage Agent** only routes. It hands off to one of three specialists.
- **Auto**, **Home** and **Travel Medical** specialists each get the same three tools: `check_coverage`,
  `open_claim` and `lookup_claim`.

The tools read a fictional policy book in `data/insurer.json` (four policies, one of them lapsed, two existing
claims), so no keys beyond OpenAI are needed. `main.py` replays three scripted customers, with no typing:

| Thread | What happens |
|---|---|
| `fender-bender` | Covered collision, then "please file it" opens claim `CL-xxxx` |
| `basement-flood` | Flood is excluded on `HM-2290`, then a status check on claim `CL-7003` |
| `er-abroad` | Emergency-room visit abroad, covered, $100 deductible |

Opik is attached with one call, `set_trace_processors([OpikTracingProcessor(...)])`, and each turn runs inside
`trace(group_id=...)` so turns of one conversation share a thread.

## See it in Opik

Open the **openai-agents-insurance-claims** project. After one run it holds **5 traces** (all named
`Claims intake`) totalling roughly **$0.001** of `gpt-4o-mini` cost.

Click the `basement-flood` trace for "Policy HM-2290. Heavy rain flooded my basement...". It has 11 spans:
a `Task` root, then the `Claims Triage Agent` with one LLM `Response` span (the model deciding to route), a
`Handoff` span, and the `Home Claims Agent` with two more LLM turns around a tool span. Click the `check_coverage`
tool span: its input is `{"policy_id":"HM-2290","peril":"flood"}` and its output is
`{"covered": false, "reason": "flood is excluded"}`. That settles the "why was I denied" question: the router
chose correctly, the specialist did check, and the data said no. If the model had paraphrased wrongly, you
would see it by comparing that output with the last LLM span's answer.

The `fender-bender` second turn shows the other half: its `open_claim` span carries the arguments the model chose
(the description and the 2300 estimate) and returns the new claim id. Each LLM span shows token usage and cost,
about 40-110 thousandths of a cent per call here.

Switch to the **Threads** tab: there are 3 rows (`fender-bender-...`, `basement-flood-...`, `er-abroad-...`).
Open `fender-bender` and both customer turns appear in order. Notice that in the second turn the triage agent runs
and hands off again, because the whole history is re-sent to the entry agent each turn. That's visible in
the second trace, and it is a cost you can only see (and then optimise) when the spans are there.

## Run it yourself

1. Start Opik locally ([install guide](https://www.comet.com/docs/opik/self-host/overview)) or create an
   Opik Cloud account.
2. `cp .env.example .env`, add `OPENAI_API_KEY` (and `OPIK_API_KEY` for Cloud). Examples at the repo root
   may share one `.env` one level up; it is found automatically.
3. `uv sync`
4. `uv run main.py` (about 40 seconds)
5. Open the project above in Opik and the Threads tab.

Offline tests, no keys or Opik needed:
`env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Remove the `Always call check_coverage` sentence from `SPECIALIST_RULES` and ask the flood question again. Does
  a `check_coverage` tool span still appear before the verdict?
- Ask about policy `HM-3318` (lapsed): the tool says "policy is lapsed" and `open_claim` refuses. Watch how the
  agent words it.
- Send an ambiguous request ("my phone was stolen on holiday abroad") and watch which specialist the
  `Handoff` span picks.
- Change one `trace(...)` call to omit `group_id`: that trace drops out of the Threads tab.

## Gotchas we hit

- **`ModuleNotFoundError: No module named 'insurer'` when running pytest.** Tests import the top-level modules
  but the project isn't an installed package. Fix: in `pyproject.toml` set
  `[tool.pytest.ini_options]` `pythonpath = ["."]`.
- **Handoffs and agents aren't `llm` or `tool` spans, and LLM spans are named `Response`.** The processor maps
  Agents SDK agent, handoff and turn spans to `general` spans; only model calls are `llm`, only function calls
  are `tool`. Filter by span type in the trace view instead of searching by agent name.
- **Traces vanish from OpenAI's own trace dashboard.** `set_trace_processors` replaces the default exporter.
  Use `add_trace_processor(OpikTracingProcessor(...))` if you want both.

## How it's put together

- `main.py` - agents, tools, the Opik processor, and the scripted conversations with thread grouping.
- `insurer.py` - plain functions for coverage checks, claim lookup and claim creation.
- `data/insurer.json` - fictional policies and existing claims.
- `tests/test_claims.py` - offline tests for coverage logic, the tools with tracking disabled, and the handoff wiring.
- `.env.example`, `pyproject.toml`, `.gitignore` - configuration.

---

*built with Opik · inspired by Opik's examples and documentation*
