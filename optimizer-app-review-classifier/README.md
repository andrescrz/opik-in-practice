# optimizer-app-review-classifier

*Let an optimizer rewrite your classifier prompt, watch the score curve climb trial by trial, and keep the winner in Opik's prompt library.*

![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat)
![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2-orange?style=flat)
![model](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat)

App-store reviews arrive as free text, and someone has to decide whether each one is a bug report, a feature request, praise, a billing complaint, or a user who is simply lost. The first prompt you write for that job is usually "pretty good" and quietly wrong: the model picks sensible categories but wraps them in explanations, so a program reading the label cannot use the answer. Fixing it by hand means reading outputs, editing words, and hoping. This example does it with a measure instead: a labeled set, an exact-match metric, and Opik's `MetaPromptOptimizer` proposing rewrites that are kept only when they score higher.

## What you'll build

A small script around Pebblepad, a made-up budgeting app. `reviews.py` holds 20 fictional reviews, four per intent, including awkward ones: praise that ends in a wish ("add a widget and it is a perfect 10"), a "how do I cancel Premium?" that sounds like billing but is really confusion. `classify.py` is a one-call gpt-4o-mini classifier whose starting prompt names the five intents and then asks for "a short note on why", which is exactly what breaks exact matching.

`main.py` then:

1. uploads the reviews as a dataset,
2. saves the starting prompt to the prompt library as version 1,
3. runs the optimizer with a budget of 8 trials (3 candidate prompts per round),
4. saves the winner as version 2 if, and only if, it beat the baseline,
5. re-scores the winner through the traced classifier as an independent check.

Everything lands in one Opik project, `optimizer-app-review-classifier`.

## See it in Opik

Open the project `optimizer-app-review-classifier`, then **Optimization runs**. The script prints a direct link to the run, pinned to this project (the generic `get_run_link()` follows whichever project the UI last had open, so it can look empty). In my run the optimization is `completed` with 9 trial experiments: the baseline scored **0.00**, the first candidate jumped to **0.85**, the second reached **0.90**, and the six remaining trials stayed at 0.90. The curve is a quick climb and then a plateau, which is a useful thing to see: it tells you the budget was more than the problem needed. The baseline scores zero because its replies carry a rationale next to the label, which exact match rejects. The winning prompt ends up saying "Provide your answer without any explanation or notes"; the remaining 10% is two reviews the labels themselves make debatable.

Open **Prompts** and find `app-review-intent-classifier`: two versions, the hand-written baseline and the optimizer's winner, with a diff between them. In the project's **Traces** tab there are 203 traces from the run: 180 `evaluation_task` traces (9 trials times 20 reviews), 3 `optimization_algorithm` traces, and 20 `classify_review` traces from the final re-score. Each `classify_review` trace nests an `llm` span (`chat_completion_create`) with token usage and cost; the `llm` spans in the project all carried usage and an estimated cost, about $0.005 in total.

The dataset `app-review-intents` appears under **Datasets** in the same project, with 20 items.

## Run it yourself

1. `cp .env.example .env` and add your `OPENAI_API_KEY` (or keep it in a `.env` higher up the tree; the app looks upward for the first one). For Opik, run a local instance (default `http://localhost:5173`) or set `OPIK_API_KEY` and `OPIK_WORKSPACE` for Opik Cloud, plus `OPIK_URL_OVERRIDE=http://localhost:5173/api/` for local.
2. `uv sync`
3. `uv run main.py` takes about a minute and costs well under a cent in model calls. Scores vary a little between runs.
4. Open the run link it prints, then the **Prompts** page.

To see the plain, untuned classifier on its own, call `classify.classify(review)` from a Python shell; with tracking on it produces one trace per call.

Offline tests (no keys, no Opik): `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change the baseline in `classify.py` to say "answer with the label only" and re-run. How much is left for the optimizer to do?
- Drop `MAX_TRIALS` to 3 in `main.py`: does the winner change, or was trial 2 enough?
- Add a sixth intent (`account_access`) with a few reviews to `reviews.py` and `LABELS`; watch which new rules the optimizer writes into the prompt.
- Loosen `normalize` so that "Bug Report" is accepted without the underscore, and compare the baseline score.

## Gotchas we hit

**Every trial scores 0.00 and the "best" prompt is the baseline.** The optimizer's reasoning model sees the metric function's name, not your intent. With the metric called `metric` it never worked out that a rationale was the problem, and all 8 trials rewrote the wording without removing it. Name the metric for what it checks and say so in the docstring: `def exact_label_match(dataset_item, llm_output)` with "1.0 only if the reply is exactly the labeled intent". The same run then reached 0.85 on the first candidate.

**An exported `OPENAI_API_KEY` beats the one in `.env`.** `python-dotenv` does not override variables that are already set, so a stale key in your shell wins and the run fails with a 401. Unset it for the run: `env -u OPENAI_API_KEY uv run main.py`.

**`{review}` versus `{{review}}`.** The optimizer's prompts use single braces, the Opik prompt library uses mustache double braces. Saving the winner unchanged stores a template that never fills in. `main.py` replaces `{review}` with `{{review}}` before `create_chat_prompt`.

**`OPIK: The project_name parameter of evaluate_optimization_trial() is deprecated`.** A harmless warning printed for each trial in opik-optimizer 3.2; the dataset's project is used. Datasets must be created with `project_name=` (as `main.py` does) so the trials land in your project and not in "Default Project".

## How it's put together

- `reviews.py`: the 20 labeled fictional reviews and the five intent labels.
- `classify.py`: the baseline prompt, the exact-match scoring helpers, and the traced classifier (`track_openai` plus `@opik.track`).
- `main.py`: dataset upload, prompt-library versions, the optimizer run, the project-pinned link, and the final re-score.
- `tests/test_app.py`: offline tests with a stubbed client, including a call to the `@track`-decorated `classify` with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
