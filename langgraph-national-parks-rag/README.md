# langgraph-national-parks-rag

*A visitor guide you can interrogate: see which pages the retriever pulled, and whether the model stuck to them.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.2-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.3.5-2f54eb?style=flat)

## The problem

A RAG assistant can give a wrong answer for two unrelated reasons: the search fetched the wrong passages, or it fetched the right ones and the model drifted away from them. The reply reads equally confident either way. This example builds a small assistant for Larkspur Hollow National Park (fictional: trails, permits, campgrounds, wildlife rules) and uses Opik to tell those two failures apart, first by looking at single traces, then by scoring a dataset with two judges.

## What you'll build

Four small modules in `parkguide/` plus a runner:

- a **corpus loader** that splits four markdown pages in `data/` into 16 sections, one per `##` heading;
- a **retriever**: BM25 keyword search written in plain Python, so it works offline and costs nothing (it also can't understand synonyms, which is the point of one test question);
- a **LangGraph graph** with two nodes, `retrieve` then `generate` (`gpt-4o-mini`, answers only from the excerpts, says "I don't know" otherwise);
- an **eval module** with an 8-question dataset and an `evaluate()` run scored by `Hallucination` and `ContextPrecision`.

`main.py` answers five demo questions, then runs the experiment twice over the same dataset, once retrieving 4 sections and once retrieving 1.

## See it in Opik

Open the `langgraph-national-parks-rag` project. After one run it holds 21 traces: 5 from the demo questions and 16 from the two experiments (8 questions each).

**A demo trace.** Click any trace named `LangGraph`. Its tree has two top-level spans that mirror the graph: `retrieve` (general) containing a `search_guide` span of type tool, and `generate` (general) containing a `ChatOpenAI` llm span with the full prompt, the token counts and an estimated cost (about $0.00006 per question). The `search_guide` span is the one to read first: its input is the question plus `k`, and its output is the sections that came back, headings included. For "How much does a backcountry permit cost and how far ahead can I book?" it returns the *Overnight backcountry permits* section, and the answer ("9 dollars per person per night ... 60 days before the trip date") matches it. The "airport shuttle" question returns an empty list, and the model replies "I don't know. Please ask at the Visitor Centre."

**The experiments.** Go to Experiments and pick the dataset `national-parks-visitor-questions`. There are two runs, `top-4-sections` and `top-1-sections`; the experiment config records `k`, the model and the retriever. Select both and compare. In the run recorded for this README, `top-4-sections` scored hallucination 0.00 and context precision 0.80, while `top-1-sections` scored hallucination 0.11 and context precision 0.80. The average hides the interesting row: the question *"Can I take my pooch on the hike up to the fire lookout?"*. BM25 has never seen "pooch" next to "dogs", so it ranks the *Fernwater Campground* section first (it matches "fire"). With four sections the right page (*Ember Ridge Trail*) is still in the list and the answer is a correct "no, dogs are not allowed" (hallucination 0.0, precision 0.8). With one section the model only sees campground rules, and hallucination jumps to 0.8 and precision falls to 0.4. Open that item in each run and click through to its trace to see the retrieved list.

The judges are LLMs, so individual scores move a little between runs (the kayak question scored 0.8 precision in one run and 0.6 in the next). Read the pooch row, not the third decimal.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have an Opik instance running (local default `http://localhost:5173`, or Opik Cloud).
2. `cp .env.example .env` and fill in `OPENAI_API_KEY`. Local Opik needs no key; for Cloud add `OPIK_API_KEY` and `OPIK_WORKSPACE` and remove `OPIK_URL_OVERRIDE`. `main.py` walks up the folder tree to the first `.env` it finds.
3. `uv sync`
4. `uv run main.py` (about a minute and roughly a cent of OpenAI usage).
5. Open the project named above in Opik.
6. Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `k=4` in `main.py`'s first `make_app` call, or the `(4, 1)` loop, to `(4, 2, 1)` and compare a third experiment against the other two.
- Add the word "pooch" to the dogs sentence in `data/trails.md` and watch the `top-1-sections` hallucination on the pooch row fall.
- Ask something the guide only half covers, e.g. "Is the Annual Pass valid at Fernwater?", and read the `search_guide` output to see what the model had to work with.
- Swap `KeywordRetriever` for an embedding retriever; keep the `@opik.track(type="tool")` on its `search` method and the trace shape stays the same.

## Gotchas we hit

**The retriever shows no span of its own.** The trace has `retrieve` and `generate` but nothing for the search. If your retriever is a LangChain `BaseRetriever` (we reproduced this with `langchain-core` 1.8.5, `langgraph` 1.2.24 and Opik 2.3.5), calling `.invoke()` inside a graph node is not logged by `OpikTracer`. Put the lookup in a function or method decorated with `@opik.track(type="tool", name="search_guide")`; it nests under the node span automatically, as in `parkguide/retriever.py`.

**`ExperimentNotFound` when you look an experiment up by name.** `client.get_experiments_by_name("top-4-sections")` raised `No experiment(s) found` even though the run had just finished: datasets and experiments here are scoped to the project they were created in. Pass it: `client.get_experiments_by_name(name, project_name="langgraph-national-parks-rag")`, and create the dataset with `get_or_create_dataset(name, project_name=...)`.

**Scores differ between identical runs.** Both metrics call an LLM judge, so re-running gives slightly different numbers per row. Compare runs on rows where the gap is large rather than on the averages.

**Experiment traces look different from the demo traces.** Inside `evaluate()` the root span is called `evaluation_task` and the graph appears as a nested `LangGraph` span under `task`, next to metric spans such as `hallucination_metric`. The `retrieve` / `generate` spans are the same; only the wrapper differs.

## How it's put together

- `main.py`: loads `.env`, sets the Opik project, wraps the graph with `track_langgraph`, runs the demo and both experiments, flushes.
- `parkguide/corpus.py`: splits markdown into `Section` objects.
- `parkguide/retriever.py`: BM25 `KeywordRetriever`; `search` is the traced tool span.
- `parkguide/graph.py`: the `retrieve` -> `generate` LangGraph and the system prompt.
- `parkguide/evaluation.py`: the 8-question dataset, `run_experiment`, score summary.
- `data/*.md`: the fictional guide (trails, permits, campgrounds, wildlife).
- `tests/test_parkguide.py`: offline tests for splitting, tokenizing, ranking, the graph with a stub model, and a traced call with tracking disabled.
- `tests/conftest.py`: turns Opik tracking off for the test run.

*built with Opik · inspired by Opik's examples and documentation*
