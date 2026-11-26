# llamaindex-syllabus-qa

*Ask a university's syllabi about late-work rules and office hours, then grade the answers section by section.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/llama--index-0.14-6a4c93?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3-2f54eb?style=flat)

## The problem

Students ask the same four things of every syllabus: how is it graded, what if I'm late, when are office
hours, and what do I need first. Each course answers differently (a dropped lab here, a hard zero there), so an
assistant that blends two syllabi gives a confident, wrong answer. This project builds that assistant over three
generated PDFs from the fictional Larkspur State University (CS 210, BIO 150, HIST 301), and uses Opik to answer
two questions: which chunks did retrieval fetch for this answer, and what share of the questions does the
assistant get right, section by section?

## What you'll build

- `pdfgen` writes the three syllabus PDFs with reportlab (committed in `data/syllabi/`, regenerated on demand).
- `index` reads them with LlamaIndex, splits them into 256-token chunks and embeds them with `text-embedding-3-small`.
- `engine` wraps a top-3 query engine on `gpt-4o-mini` and returns the answer plus the source chunks.
- `suite` is an Opik test suite: 11 questions tagged by syllabus section (grading, late work, office hours,
  prerequisites, plus one not covered by any syllabus), each with plain-English assertions, run 3 times per item.
- `cli` ties it together: `generate`, `ask "..."`, `demo`, `suite`.

## See it in Opik

Open the **llamaindex-syllabus-qa** project. A `query` trace has one `retrieve` span (containing an `embedding`
span for the question) and one `synthesize` span (with `chunking`, `templating` and an `llm` span). The `retrieve`
output lists the chunks that came back; the `llm` span shows the prompt with those chunks and the token usage
and cost (about $0.00016 for a typical answer). In my run, "When and where are Dr. Nandakumar's office
hours?" retrieved chunks from all three syllabi, so you can see the retriever wasn't sure which course
you meant even though the answer came out right.

Each command also leaves an `index_construction` trace for building the index, so after `demo` plus `suite` the
project holds 39 traces: 4 `query`, 2 `index_construction` and 33 `evaluation_task`.

Under **Experiments** (or the project's test suites) open the newest run of `llamaindex-syllabus-qa`. My run
passed **9 of 11 items (82%)**:

| section | passed |
|---|---|
| grading | 3/3 |
| prerequisites | 2/2 |
| not covered (calculator policy) | 1/1 |
| late work | 2/3 |
| office hours | 1/2 |

The two failures are instructive. For "When and where are Dr. Nandakumar's office hours?" the answer was
correct but began "The course is HIST301 - Atlantic World". That label comes from the PDF's file name, which
LlamaIndex adds to each chunk as metadata and the model reads, so the judge ruled that the course code was not
in the excerpts. The BIO 150 notebook question failed the same way. Click a failed item to see the judge's
reason per assertion and open the linked `evaluation_task` trace to inspect the chunks. The suite has 33
`evaluation_task` traces (11 items x 3 runs); each contains the same retrieve/synthesize tree. An item passes
when 2 of its 3 runs pass. The rate is a snapshot: a judge is an LLM, so expect it to move by an item or two.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have a local Opik running (the default is `http://localhost:5173`),
   or use Opik Cloud.
2. `cp .env.example .env` (or use a `.env` in a parent folder) and set `OPENAI_API_KEY`. For local Opik add
   `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`; for Opik Cloud add
   `OPIK_API_KEY` and `OPIK_WORKSPACE`.
3. `uv sync`
4. `uv run python -m syllabus_qa demo` (four questions, four traces)
5. `uv run python -m syllabus_qa suite` (the pass rate, per item and per section, and a link to the run)

Both together take about 95 seconds and well under a dime in OpenAI usage. Try your own question with
`uv run python -m syllabus_qa ask "Is there a final exam in HIST 301?"`.

## Poke around

- Set `TOP_K = 1` in `syllabus_qa/config.py` and re-run `suite`: the questions that name a course but share
  vocabulary with the others start to fail first.
- In `pdfgen.py` change CS 210's final-exam weight from 20% to 25%, run `python -m syllabus_qa generate`, then
  `suite`. Assertions pinned to the old number fail, and nothing else does.
- Add a question about a policy no syllabus mentions to `ITEMS` in `suite.py` and see whether the answer admits
  it, like the calculator item does.
- Change `EXECUTION_POLICY` to a single run and compare how stable the pass rate is.

## Gotchas we hit

**Symptom: the answers are nonsense or the retrieved chunks look like `%PDF-1.4 ... obj <<`.**
Cause: the `llama-index` meta-package no longer ships file readers, and `SimpleDirectoryReader` doesn't
complain; it falls back to reading the PDF's raw bytes as text. Fix: add the reader package explicitly:
`"llama-index-readers-file>=0.7.0"` in `pyproject.toml`.

**Symptom: `ValueError: No files found in .../data/syllabi.` although the PDFs are there.**
Cause: `SimpleDirectoryReader` skips paths that contain a hidden (dot-prefixed) folder anywhere in the
absolute path, for example a checkout inside `~/.worktrees/`. Fix: pass the files, not the folder:
`SimpleDirectoryReader(input_files=sorted(data_dir.glob("*.pdf")))`.

**Symptom: traces appear under "Default Project".**
Cause: the project name is read when the first Opik client is created, so it must be set after loading `.env`
and before any Opik call. Fix: `os.environ.setdefault("OPIK_PROJECT_NAME", ...)` in `config.py`, which every
module imports first. Pass `project_name=` to `get_or_create_test_suite` too, so the suite's experiments land in
the same project.

## How it's put together

- `syllabus_qa/config.py`: loads `.env`, sets the Opik project, holds model and chunking settings.
- `syllabus_qa/pdfgen.py`: the three fictional syllabi as PDFs.
- `syllabus_qa/index.py`: reads the PDFs and builds the vector index.
- `syllabus_qa/engine.py`: the query engine and `ask`, which returns answer plus sources.
- `syllabus_qa/tracing.py`: turns on Opik's LlamaIndex handler and flushes at exit.
- `syllabus_qa/suite.py`: the test suite items, assertions, execution policy and summary printing.
- `syllabus_qa/questions.py`, `cli.py`, `__main__.py`: demo questions and the command line.
- `data/syllabi/`: the generated PDFs, committed so a run never depends on generation.
- `tests/test_offline.py`: five offline tests (PDF generation, `ask`, suite shape, section summary, tracing with
  tracking disabled). Run `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

---

*built with Opik · inspired by Opik's examples and documentation*
