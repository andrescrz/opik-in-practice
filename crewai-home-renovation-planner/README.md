# crewai-home-renovation-planner

*Three CrewAI agents plan a kitchen and bath renovation, and Opik tells you which one spent the money.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/crewai-1.15%2B-FF5A50?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

A crew hands you one finished plan, and the plan hides everything that produced it. You can't tell which agent used the most tokens, what each one was given, or what the whole thing cost. This example wraps a small CrewAI crew with Opik's `track_crewai` so that a single `kickoff` becomes a single trace, with token counts and dollar cost on the model calls underneath. A short script then totals them per agent.

## What you'll build

A sequential crew on `gpt-4o-mini` that works for a fictional household in Maple Court, unit 4B:

1. **Scope Planner** reads `data/brief.md` and lists the kitchen and bathroom work.
2. **Budget Estimator** prices that scope from `data/price_sheet.csv` and checks it against a 38,000 USD ceiling.
3. **Schedule Coordinator** sequences the work around lead times, elevator bookings, building hours and the owners' trip.

Everything is offline (no search tools), so one run takes about a minute and costs under a tenth of a cent. The code is a small package rather than one script: agents, tasks and crew assembly live in separate modules, with a CLI on top.

## See it in Opik

Open the project **crewai-home-renovation-planner** and go to **Traces**. A run produces exactly one trace named `kickoff`. Its estimated cost is about $0.00085 and it used 3,101 tokens (2,239 prompt, 862 completion).

Expand it. Under `kickoff` there is one span per task: `Task: Define the scope`, `Task: Estimate the budget`, `Task: Plan the schedule`. Each holds a span named after its agent, and inside that CrewAI's internal reasoning loop (`Flow.kickoff_async`, `call_llm_and_parse`, `finalize`, ...), 49 spans in all. The only `llm` spans are the `chat_completion_create` calls, three in this run, one per agent. Click one: it shows model `gpt-4o-mini-2024-07-18`, token usage and an estimated cost. The kickoff trace's root input and output hold the brief and the final schedule.

The per-agent numbers from that run:

| Agent | Tokens | Cost |
|---|---|---|
| Schedule Coordinator | 1,593 | $0.00039 |
| Budget Estimator | 1,015 | $0.00034 |
| Scope Planner | 493 | $0.00012 |

The coordinator is the most expensive because it receives the brief, the price sheet and both upstream outputs. To reproduce the table, run `uv run renovation-costs` after a run.

## Run it yourself

1. `cp .env.example .env`, add `OPENAI_API_KEY`, and point `OPIK_URL_OVERRIDE` at your Opik (the default is a local install; for Opik Cloud use `https://www.comet.com/opik/api` and set `OPIK_API_KEY`). A `.env` in any parent folder works too.
2. `uv sync`
3. `uv run renovation-planner`
4. `uv run renovation-costs` to print tokens and cost per agent for the latest trace.
5. Open the `crewai-home-renovation-planner` project in Opik and expand the newest trace.

Tests need no keys and no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Open the `Schedule Coordinator` llm span and read its input next to its output. In our run the plan put demolition on Feb 26 to Mar 2 even though the brief confines noisy work to the owners' trip (2 to 15 March), and it ran into a fourth week. The span shows the model had the constraint in front of it.
- Edit `data/brief.md` (a lower ceiling, a second bathroom) and re-run: compare the budget estimator's span cost across traces.
- Set `MODEL` in `renovation_planner/agents.py` to a bigger model for the schedule coordinator only, then compare per-agent cost with `renovation-costs`.
- Pass your own brief with `uv run renovation-planner --brief path/to/brief.md`.

## Gotchas we hit

**The agent spans have no cost.** Symptom: in the SDK or the trace tree, `Scope Planner`, `Budget Estimator` and `Schedule Coordinator` show no usage or cost, only the trace root does. Cause: Opik records usage on `llm` spans, and CrewAI's agent spans are general spans. Fix: sum the llm spans under each agent, as `renovation_planner/costs.py` does (walk `parent_span_id` up to the span whose parent is a `Task: ...` span).

**Traces land on the wrong Opik server.** Symptom: the run succeeds but the local project stays empty. Cause: the Opik client reads `~/.opik.config` (which may point at another server) unless env vars override it. Fix: load the `.env` with `OPIK_URL_OVERRIDE` before the first Opik client is created, as `cli.py` and `costs.py` do:

```python
load_dotenv(find_dotenv(usecwd=True))  # before track_crewai or opik.Opik() runs
```

## How it's put together

- `renovation_planner/agents.py` — the three agents and the model name.
- `renovation_planner/tasks.py` — the three sequential tasks and their context chain.
- `renovation_planner/crew.py` — assembles the crew and calls `track_crewai` with the project name.
- `renovation_planner/inputs.py` — loads the brief and renders the price sheet.
- `renovation_planner/cli.py` — the `renovation-planner` entry point; flushes Opik before exit.
- `renovation_planner/costs.py` — the `renovation-costs` roll-up of tokens and cost per agent.
- `data/` — the fictional brief and price sheet.
- `tests/test_planner.py` — offline tests: inputs, task wiring, CLI args, building a traced crew with tracking disabled, the cost roll-up on stub spans.

---

*built with Opik · inspired by Opik's examples and documentation*
