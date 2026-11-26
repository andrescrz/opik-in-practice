# dspy-board-game-rules-qa

*A rules-lawyer bot for a made-up board game that teaches itself the house answer format, and a test suite that proves it.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![DSPy](https://img.shields.io/badge/DSPy-3.x-8B0000)
![Opik](https://img.shields.io/badge/Opik-2.3.6-2f54eb)

Rules questions have a right answer and a right *shape*: every reply should be one short phrase followed by the rule it comes from, like `1 oil token [§2.3]`. You can beg for that shape in a prompt, or you can show the model a few worked examples. DSPy's optimizers automate the second route, but "the optimizer helped" is only a claim until you run the same checks before and after. This example makes that comparison concrete: one test suite, two runs, and the traces to explain the difference.

## What you'll build

A small Python package, `rules_qa`, around **Lanternfall**, a fictional lamplighter game whose rulebook lives in `data/rulebook.md` (eleven numbered sections). A `dspy.ChainOfThought` program on `gpt-4o-mini` answers questions about it. Its signature never mentions the citation format. Instead:

- `rules-qa compile` runs `dspy.BootstrapFewShot` over eight answered training questions, scored by a regex metric (trailing `[§x.y]`, right section, key fact present), and keeps four self-generated demos.
- `rules-qa run` builds an Opik test suite of eight held-out questions with LLM-judged assertions, runs it against the raw program, compiles, and runs the identical suite again.
- `OpikCallback` traces every DSPy call, including the compile phase.

## See it in Opik

Open the project **dspy-board-game-rules-qa**. In my run it holds 23 traces: 16 `evaluation_task` traces (8 per suite run) and 7 `ChainOfThought` traces from the compile phase.

**The comparison.** The suite `lanternfall-rules-qa` has two experiments, `uncompiled` and `compiled`. Uncompiled scored **0/8 (0%)**; compiled scored **6/8 (75%)** on the same items and assertions. The per-assertion breakdown for the compiled run was 8/8 on "ends with a `[§x.y]` citation", 7/8 on "cites the right section" and 7/8 on "otherwise one short phrase". The raw program knew the answers ("The youngest player takes the first turn.") but 0 of its 8 answers carried a citation; all 8 compiled answers did. Two compiled answers still ran long, so 75% is the honest number, not 100%. LLM judges wobble, so expect a run or two to differ by an item.

**The prompt that changed.** Open an `evaluation_task` trace from each run and expand `answer > ChainOfThought > Predict > LM: openai - gpt-4o-mini`. The uncompiled LM input is about 3,000 characters: the rulebook and the question. The compiled one is about 9,900 characters, because four complete worked examples (question, reasoning, `[§x.y]` answer) now sit in front of it. Nothing in the signature changed; the demos are the whole difference, and they are right there in the span.

**The program graph.** The seven `ChainOfThought` traces come from `BootstrapFewShot` running the program over the trainset. These are the teacher attempts the optimizer judged, and (with `log_graph=True`) each carries the module graph, so Opik can draw the program. Seven attempts rather than eight: the compiler stops once it has its four passing demos.

Cost for the whole run: roughly $0.012 in Opik's estimate, about 50 seconds end to end.

## Run it yourself

1. `cd dspy-board-game-rules-qa && cp .env.example .env`, then add `OPENAI_API_KEY`. The default Opik URL targets a local self-hosted Opik on :5173; for Opik Cloud add `OPIK_API_KEY` and drop the URL override.
2. `uv sync`
3. `uv run rules-qa run` — the full before/after comparison.
4. Try single questions: `uv run rules-qa ask "Who goes first?"`, then `uv run rules-qa ask --compiled "Who goes first?"` (uses the program saved by the compile step).
5. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `max_bootstrapped_demos` in `compile.py` to 1 and re-run. How much of the format does one demo buy, and do the long answers get worse?
- Add "Answer in one short phrase" to the signature docstring and run the *uncompiled* suite. Does an instruction alone fix the citation, or do you still need the demos?
- Remove the key-fact check from `format_and_citation` and recompile. Which demos does the optimizer now accept, and which assertion decays?
- Add a question the rulebook cannot answer, with an assertion that the bot says so. Neither signature nor demos cover refusals.

## Gotchas we hit

**Symptom:** the console prints `You are attempting to log data into a nested span under the project name "dspy-board-game-rules-qa". However, the project name "Default Project" from parent span will be used instead.`

**Cause:** the `@opik.track` function that wraps the DSPy call opens its span before `OpikCallback`'s spans, and without an explicit project it resolves to the default one, which then disagrees with the callback.

**Fix:** name the project on the decorator as well as on the callback:

```python
@opik.track(name="answer", type="general", project_name=PROJECT_NAME)
def answer(program, question): ...
```

## How it's put together

- `data/rulebook.md`: the fictional rulebook, one `## §x.y` heading per rule.
- `rules_qa/__init__.py`, `config.py`: load `.env` before anything imports Opik; project and model constants.
- `rules_qa/rulebook.py`: loads the rulebook and lists its section ids.
- `rules_qa/signatures.py`: the DSPy signature (deliberately silent about the format).
- `rules_qa/program.py`: `OpikCallback` setup, the ChainOfThought program, the traced `answer` function.
- `rules_qa/data.py`: eight training examples and eight held-out test questions.
- `rules_qa/metric.py`: the programmatic compile-time metric and citation parser.
- `rules_qa/compile.py`: the `BootstrapFewShot` step; saves `compiled/program.json`.
- `rules_qa/suite.py`: the Opik test suite and the side-by-side runs.
- `rules_qa/cli.py`: `ask`, `compile`, `run`.
- `tests/test_rules_qa.py`: offline tests for parsing, the metric, data integrity, and a traced call with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
