# opik-py-redaction-pipeline

*Scrub personal data out of documents in three steps, and build every Opik trace by hand to see exactly what the integrations do for you.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3%2B-2f54eb?style=flat)
![OpenAI](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat)

Redaction is a pipeline where one number matters: how much personal data is still in the output. A single LLM span cannot tell you that. You need to see which step caught what, what the checker thought, and whether the checker was right. This example redacts three fictional documents (a tenant's complaint letter, a clinic intake note and a community-centre incident report) and records each run with the plain `opik` client: no decorators, no OpenAI wrapper. Every trace, span, token count and score comes from a call you can point at in `main.py`.

## What you'll build

```
document -> trace "redact-document"
  |- regex-pass            tool        emails, phones, SSNs, ID numbers, dates of birth
  |- contextual-pass       general     one gpt-4o-mini call finds names, addresses, employers
  |   '- find-contextual-pii   llm     model, provider, token usage recorded by hand
  '- verify                guardrail   a second gpt-4o-mini call audits the masked text
      '- audit-redacted-text   llm     leftovers are masked too
trace feedback scores: redaction-confidence, leaked-pii-count
```

Each document carries a list of the PII planted in it, so the run can count what survived. That count is ground truth the pipeline itself never sees.

## See it in Opik

Open the `opik-py-redaction-pipeline` project. The trace list has three rows, one per document (tagged `tenant-letter`, `clinic-intake`, `school-incident`), each costing roughly $0.0002 for 630-710 tokens, with two feedback columns: `redaction-confidence` and `leaked-pii-count`.

Open the `school-incident` trace. Its `leaked-pii-count` is **1**: "Mrs. Oyelaran" went through all three steps. The first model call masked "Marguerite Oyelaran" but missed the honorific form, and the auditor did not flag it either, so the `verify` span's output still contains it. The score's reason names the string. The other two traces show 0.

Expand the tree. `regex-pass` is a `tool` span whose output lists what it matched (`{'EMAIL': 1, 'ID': 1}`). `contextual-pass` is a `general` span with `find-contextual-pii` nested under it. That child is an `llm` span with model `gpt-4o-mini-2024-07-18`, provider `openai`, 220 prompt / 120 completion tokens and a cost of about $0.0001, all taken from the response and set by hand. `verify` is a `guardrail` span wrapping `audit-redacted-text`; its output carries `auditor_confidence`, which is where the trace's `redaction-confidence` comes from.

Two things to notice, because they are honest limits of this pipeline. The auditor's confidence is low (0.1 to 0.5) even when nothing leaks: it scores the text it was shown, before `verify` masks what it found, so a low score means "I had to fix things", not "the output is unsafe". And the tenant letter's "Since November 3" came back as `Since [ORG]`: the model over-reported a date as an organisation, and the span input/output pair shows exactly where.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have an Opik instance running (local default `http://localhost:5173`, or Opik Cloud).
2. `cp .env.example .env` and fill in `OPENAI_API_KEY` (add `OPIK_API_KEY` for Cloud).
3. `uv run python main.py` redacts the three documents (about 13 seconds, under a tenth of a cent) and writes results to `out/`.
4. Open the `opik-py-redaction-pipeline` project in Opik.
5. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Sort the trace list by `redaction-confidence` and then by `leaked-pii-count`. The two orderings disagree (the 0.2 trace leaks, the 0.1 one does not), which is the argument for keeping a ground-truth score beside the model's own.
- Remove `model=`, `provider=` or `usage=` from the llm span in `traced_ask` and re-run: the span still appears but its cost cell goes empty.
- Add `os._exit(0)` right before `opik_client.flush()` and run again: the script prints results and the traces never arrive, because nothing flushed the queue.
- Add a fourth document with a nickname or a street name written in lowercase and see which step, if any, catches it.

## Gotchas we hit

**Spans arrive with no name or type, and a warning says `Calling Span.end() shortly after creation with batching enabled may cause data loss`.** Creating a span with `trace.span(...)` and finishing it with `span.end(...)` a moment later sends two messages that the batcher can reorder; some spans were stored blank (name `None`) in our first run. Create each span once, already finished: `opik_client.span(trace_id=..., id=..., start_time=..., end_time=..., input=..., output=...)`, generating ids up front with `opik.id_helpers.generate_id()` so children can reference a parent that is sent later.

**`OPIK_TRACK_DISABLE=true` does not stop the traces.** It switches off `@track` and the integrations, but `opik.Opik().trace()` and `.span()` still send. A first version of the tests built a real client and wrote stub data into the project. The tests here inject a recording stand-in for the client instead.

**The email rule masked the sentence's full stop (`Mail [EMAIL] Ana Ruiz`).** The pattern `[\w.+-]+@[\w-]+\.[\w.-]+` ends on `.`-or-word characters and swallowed the trailing period. The fixed pattern `[\w.+-]+@[\w-]+(?:\.[\w-]+)+` must end on a word character; `tests/test_redact.py` covers it.

**Asking a model to list leftovers returns placeholders and whole sentences.** Given `[NAME]` in the text, the auditor listed `[NAME]` as "remaining" and set confidence to 0, and the contextual pass once returned a sentence-long span that wiped half a document. `apply_findings` in `redact.py` skips anything containing `[` or longer than ten words.

## How it's put together

- `main.py`: the pipeline, the model calls, every trace, span, usage and score call, and the flush.
- `redact.py`: pure logic: regex rules, applying findings, the leak counter, JSON parsing. No model, no Opik.
- `data/documents.json`: three fictional documents with their planted PII.
- `tests/test_redact.py`: unit tests for the regex rules, masking order, skipped findings and the leak counter.
- `tests/test_pipeline.py`: runs `redact_document` with a stubbed OpenAI client and a recording Opik stand-in; asserts span types, usage and scores.
- `.env.example`, `pyproject.toml`, `.gitignore`: configuration.

---

*built with Opik · inspired by Opik's examples and documentation*
