# smolagents-solar-energy-analyst

*Ask an agent about a solar farm, then read the pandas it wrote to find out whether to believe it.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![smolagents 1.26](https://img.shields.io/badge/smolagents-1.26-FFD21E?style=flat)
![OpenTelemetry](https://img.shields.io/badge/export-OTLP%20to%20Opik-2f54eb?style=flat)

## The problem

An agent that answers with prose can be wrong in words. An agent that answers by
*writing and running Python* is wrong in numbers, and a number computed by code
looks authoritative whether or not the code measured the right thing. Reading
only the final answer, you cannot tell the difference.

Here the data is a fictional solar farm, Meadowbrook Solar: four arrays (A-D),
91 days (April 1 to June 30, 2025), one row per array per day with `kwh`,
`irradiance_kwh_m2` and `inverter_faults`. Three anomalies are planted in it:

1. **Array C** loses about 35% of its output per unit of sunshine from May 14, with irradiance unchanged.
2. **Array B** logs 27 inverter faults over June 3-6 and nearly stops producing.
3. **May 21**: every array reports 0 kWh on a sunny day (irradiance 7.1).

## What you'll build

A smolagents `CodeAgent` on `gpt-4o-mini` that is asked one question per anomaly.
For each it loops think, write pandas, execute, observe. The local executor is
restricted to `pandas` as the only extra import. Tracing uses the OpenInference
`SmolagentsInstrumentor` and a plain OTLP/HTTP exporter aimed at Opik; there is
no tracing code inside the agent logic. `data/solar_farm.csv` is committed
(seeded generator: `make_data.py`).

## See it in Opik

Open the **smolagents-solar-energy-analyst** project: three traces, all named
`CodeAgent.run`, newest first (so the May 21 question is on top). In my run:

- The array-C question has 8 spans: the run, three `OpenAIModel.generate` calls and three `Step` spans, plus the final-answer tool. The fault-burst question took four steps (10 spans); the May 21 one took two (6 spans).
- Click an `OpenAIModel.generate` span. Its output holds the model's reasoning plus the exact pandas it proposed, e.g. `data['kwh'] / data['irradiance_kwh_m2']` grouped per array before and after 2025-05-14.
- Click the matching `Step` span. Its output starts with `Execution logs:` followed by what the code printed, for example `{'A': (838.94, 827.11), 'B': (776.42, 694.84), 'C': (798.15, 516.58), 'D': (744.60, 728.56)}`.

That pairing caught a real error. The agent's final answer for the first
question named the right array and the right ratios (798.15 to 516.58), but
said the drop started **April 5**, when the planted change is May 14. The trace
shows why: step 2 defined "drop start" as the first day each array's yield fell
below its pre-May mean, a noisy criterion that fires in the first week of April
for every array (the printed log is `A: 04-03, B: 04-05, C: 04-05, D: 04-01`).
The answer was confident and half wrong, and only the spans explain it. LLM
output varies between runs, so yours may differ; the other two questions
(Array B, June 3-6, 27 faults, 124.1 kWh mean; May 21 at irradiance 7.1) came
back correct in my run.

## Run it yourself

1. Have an Opik instance running (local default `http://localhost:5173`) or an Opik Cloud key.
2. `cp .env.example .env` (or use a repo-level `.env`) and set `OPENAI_API_KEY`. For Cloud, also set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api/` and `OPIK_API_KEY`.
3. `uv sync`
4. `uv run main.py` (about 40 seconds, well under one cent of gpt-4o-mini)
5. Open the project above in Opik.

Tests, offline: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Re-run and compare the "start date" answer across runs; find the step where the model picks its criterion.
- Reword question 1 to say "split at 2025-05-14 and compare daily yield" and see whether the date answer becomes right.
- Regenerate the CSV with another seed or move the Array B burst in `make_data.py`, then see whether the agent finds it.
- Drop `"pandas"` from `additional_authorized_imports` and watch the executor error in a `Step` span.

## Gotchas we hit

**Token usage shows twice what you spent.** The trace-level usage reads e.g.
`total 26470` when the model calls add up to 13235. Cause: the instrumentor
records the aggregate usage on the `CodeAgent.run` span (typed `llm`) as well as
on each `OpenAIModel.generate` span, and Opik sums them all. Fix: read tokens
from the `generate` spans, or from the `run` span alone, not the trace total.

**`total_estimated_cost` is empty.** Raw OTLP spans carry token counts and a
model name (`gpt-4o-mini`) but no provider attribute Opik recognises, so no
dollar figure is derived (I did not try mapping one). Usage is there; compute cost yourself
from the `generate` spans, or add a provider attribute if you need Opik to.

## How it's put together

- `main.py` - the briefing, three questions, the `CodeAgent` with `pandas` authorized, and the flush on exit.
- `tracing.py` - builds the Opik OTLP endpoint and headers from env, installs the instrumentor.
- `make_data.py` - seeded generator for the planted anomalies.
- `data/solar_farm.csv` - 364 rows of fictional production data.
- `tests/test_data.py` - confirms each anomaly is really in the CSV.
- `tests/test_tracing.py` - endpoint and header construction.
- `tests/test_agent.py` - an instrumented agent runs against a stub model, no network.

---
*built with Opik · inspired by Opik's examples and documentation*
