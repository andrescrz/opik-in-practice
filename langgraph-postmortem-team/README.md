# langgraph-postmortem-team

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.x-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3-2f54eb?style=flat)

*Three LangGraph agents turn a messy outage into a blameless post-mortem, and Opik shows you who did what, and what each one cost.*

Nobody enjoys writing the post-mortem. The evidence is scattered across a timeline, an alert history, gateway logs and a chat channel, and the draft is only as good as the questions someone thought to ask. Automating it with several agents helps, but it also hides the question you will ask when the draft is wrong: was it the plan, one investigation pass, or the write-up?

## What you'll build

A small Python package, `postmortem/`, that runs a LangGraph team over a fictional outage (INC-2291: a checkout outage at an imaginary payments company, 84 minutes long):

```
planner ──> investigator ──┐
                ^          │ questions left? loop
                └──────────┘ all answered? ──> writer ──> post-mortem
```

- **planner** splits the investigation into 3-4 questions (structured output).
- **investigator** answers one question per pass from the artifacts in `data/` (timeline, alerts, gateway logs, chat excerpts, process docs), using a tiny rarity-weighted keyword search. No vector store, no web.
- **writer** produces the blameless post-mortem: summary, impact, timeline, contributing factors, action items, with roles instead of names.

All agents use `gpt-4o-mini`. The compiled graph is wrapped once with Opik's `track_langgraph`.

## See it in Opik

Open the **langgraph-postmortem-team** project and click the trace from your run. In my verified run there was exactly one trace with 19 spans:

- one `planner` span, four `investigator` spans (one per loop pass) and one `writer` span, each with a `ChatOpenAI` llm span inside (six llm spans in total), plus small `route_investigation` spans for each loop decision;
- the trace's graph view draws planner, investigator with its self-loop, and writer, so the loop is visible and not just implied by four repeated spans;
- every llm span carries tokens and an estimated cost. Grouping them by the node that made the call gave: planner $0.00009 (328 tokens), investigator $0.00046 over four passes (1,539 tokens), writer $0.00049 (1,392 tokens). The whole team cost about $0.001 per run, and the writer costs as much as all four investigation passes put together.

Click into an `investigator` span to see the question going in, the artifact chunks it retrieved and the sourced answer coming out. That is how you debug a draft: if the post-mortem misses the root cause, check whether the planner asked about it, then whether the investigator's chunks contained it.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (a parent folder's `.env` also works).
2. Point at Opik. For a local self-hosted stack, `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default` in the same `.env`. For Opik Cloud, set `OPIK_API_KEY` and `OPIK_WORKSPACE` instead.
3. `uv sync`
4. `uv run main.py` (about 20-40 seconds; `uv run postmortem "your own prompt"` also works).
5. Open the trace in the project above.

Tests run offline, with no keys: `OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Ask a narrower question: `uv run main.py "Why did the alerts not reach the payments on-call?"` and compare the planner's questions and the cost split.
- Edit the planner prompt in `postmortem/nodes.py` to ask for exactly two questions; the trace gets two investigator spans and the cost drops with them.
- Delete the maintenance-window note from `data/alerts.md` and see whether the post-mortem admits the gap or invents a reason.
- Change `search(...)`'s `k` in `postmortem/nodes.py` and watch the investigator's input tokens move.

## Gotchas we hit

- **The post-mortem never names the root cause.** My first run described alerts and retries in detail but never mentioned the pool size. The planner had asked "what changes were made to the checkout system?", vague words that matched the wrong chunks, so the investigator's excerpts did not contain the config change. The fix was in the planner prompt: tell it to phrase questions in the artifacts' own terms (`releases, config values, rollbacks, alert names, pool sizes`). Opik's `investigator` span inputs made this obvious in seconds.
- **Traces go to the wrong server or project.** `dotenv.load_dotenv` does not override variables already exported in your shell, and the Opik client reads its settings when it is created. Load `.env` (and set `OPIK_PROJECT_NAME`) before creating any Opik object, as `postmortem/cli.py` does, and unset stale exported keys.
- **Unit tests that import the traced graph.** The wrapper does not get in the way: with `OPIK_TRACK_DISABLE=true` the traced graph runs normally (see `test_traced_graph_still_runs_with_tracking_disabled`).

## How it's put together

- `main.py` - thin entry point, calls `postmortem.cli.main`.
- `postmortem/state.py` - the shared graph state.
- `postmortem/corpus.py` - loads `data/` into chunks and ranks them for a query.
- `postmortem/nodes.py` - planner, investigator, loop router and writer.
- `postmortem/graph.py` - wires the graph.
- `postmortem/cli.py` - the CLI and the Opik wiring (tracer, `track_langgraph`, flush).
- `data/` - fictional INC-2291 artifacts: timeline, alerts, gateway logs, chat excerpts, process docs.
- `tests/test_postmortem.py` - offline tests with a stubbed model: retrieval, loop routing, graph run, and a traced run with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
