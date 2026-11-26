# temporal-ts-grant-review

*A grant application is reviewed by two OS processes, and Opik shows it as one trace, flaky retry included.*

![Node](https://img.shields.io/badge/node-20.3%2B-5FA04E?logo=nodedotjs&logoColor=white)
![Temporal](https://img.shields.io/badge/Temporal_TS_SDK-1.13%2B-000000?logo=temporal&logoColor=white)
![OpenAI](https://img.shields.io/badge/openai-gpt--4o--mini-412991?logo=openai&logoColor=white)

The Alderbrook Neighborhood Fund (fictional) hands out small community grants. Reviewing an application
means a few steps that can each fail on their own: a rules check, a call to a ledger service that sometimes
drops the connection, an LLM-written summary for the human reviewer, and a decision. Temporal makes that
durable. The catch is that a client starts the workflow and a separate worker runs it, so no single process
ever sees the whole review. This example wires Opik into both processes so you get one trace per application
and can see what failed, what retried and what the model said.

## What you'll build

A `reviewApplication` workflow with four activities:

1. `checkEligibility`: fund-area, grant cap and audience-size rules (pure code).
2. `checkBudget`: verifies the budget lines add up. It throws on its first attempt on purpose, and the
   workflow's retry policy makes attempt 2 succeed.
3. `writeReviewerSummary`: one `gpt-4o-mini` call that writes the reviewer's summary.
4. `recordDecision`: maps the checks to `approve`, `revise-and-resubmit` or `decline`.

Three fictional applications go through it: a clean one, one whose budget lines total $3,600 against a $4,800
request, and one from outside the fund area (it skips the budget check). One command (`npm run demo`) starts
a Temporal dev server, a worker process and the client, then shuts them all down.

Tracing uses Temporal's OpenTelemetry interceptors on the client and on the worker, both exporting OTLP to Opik's
endpoint with the same project name. The interceptors pass trace context through Temporal's own headers, which
is what joins the two processes into a single trace.

## See it in Opik

Open the `temporal-ts-grant-review` project and the Traces tab. After a run you will find three traces named
`review:GRANT-201`, `review:GRANT-202` and `review:GRANT-203`. Open `review:GRANT-201` and expand the tree:

- The root `review:GRANT-201` and `StartWorkflow:reviewApplication` come from the **client** process. Every
  span under `RunWorkflow:reviewApplication` comes from the **worker** process.
- Each activity has a `StartActivity:*` span (the workflow scheduling it) and a `RunActivity:*` span per attempt.
  `checkBudget` has **two** `RunActivity` spans: the first carries the error `Ledger service unavailable:
  connection reset`, the second is clean. The trace as a whole still succeeds, so the retry is only visible if you
  look inside.
- Under `RunActivity:writeReviewerSummary` sits a `reviewer-summary` span of type `llm` with model
  `gpt-4o-mini-2024-07-18`, the prompt and reply, and token usage (170 prompt, 66 completion for GRANT-201).
  Opik prices it at about $0.00007, and each trace carries that as its cost.

The traces have 13, 13 and 10 spans: GRANT-203 is shorter because an ineligible application never reaches
`checkBudget`, so compare it with the others to see the workflow's branch. On `review:GRANT-202` read the summary:
it calls out the $3,600 vs $4,800 mismatch that `checkBudget` found.

## Run it yourself

You need Node 20.3+, the [`temporal` CLI](https://docs.temporal.io/cli) on your PATH (no Docker), an OpenAI key and
an Opik instance (local default `http://localhost:5173/api/`, or Opik Cloud).

1. `cp .env.example .env` and fill in `OPENAI_API_KEY` (and `OPIK_API_KEY` for Cloud). A `.env` in a parent
   folder also works.
2. `npm install`
3. `npm run demo`. The dev server defaults to port 7233; pick others with
   `TEMPORAL_DEV_PORT=7243 TEMPORAL_DEV_UI_PORT=7244 npm run demo`. It takes about 15 seconds.
4. Open the project in Opik.

To run the pieces yourself against any Temporal server: `npm run worker` in one terminal, `npm run client` in another
(both honor `TEMPORAL_ADDRESS`).

Tests: `npm test`. Set `OPIK_TRACK_DISABLE=true` to make `setupTracing` a no-op and skip exporting.

## Poke around

- In `src/activities/index.ts` change `attempt === 1` to `attempt <= 3` and count the red `RunActivity:checkBudget`
  spans in the trace (three red, one green).
- Change `maximumAttempts` in `src/workflows/index.ts` to `2` and the failure count to `attempt <= 2`: the workflow
  now fails, and the trace ends in an error status instead of a verdict.
- Edit `MAX_GRANT` in `src/activities/rules.ts` to 3000 and watch GRANT-201 flip from `approve` to `decline`,
  with the reason showing up in the summary span's input.
- Start the worker on its own with `OPIK_TRACK_DISABLE=true npm run worker` (and the client normally) and compare: only the client spans arrive.

## Gotchas we hit

- **Symptom:** the `writeReviewerSummary` activity fails with an invalid-API-key error even though `.env` has a fresh key.
  **Cause:** `dotenv` never overrides variables already exported in your shell, so a stale `OPENAI_API_KEY`
  (or a proxy `OPENAI_BASE_URL`) wins over the file. **Fix:** `env -u OPENAI_API_KEY -u OPENAI_BASE_URL npm run demo`,
  or unset them in your shell. The app also deletes `OPENAI_BASE_URL` at startup so it always calls the public API.
- **Symptom:** the worker exits immediately with a connection error when launched by a script.
  **Cause:** it started before the dev server was listening. **Fix:** `scripts/demo.ts` polls the server with
  `Connection.connect` and only then spawns the worker.

## How it's put together

- `scripts/demo.ts`: starts `temporal server start-dev`, the worker process, runs the client, stops everything.
- `src/client.ts`: the Temporal client; opens the root `review:*` span and starts each workflow.
- `src/worker.ts`: the worker process with the OpenTelemetry interceptors and the workflow span sink.
- `src/workflows/index.ts`: the `reviewApplication` workflow and its retry policy.
- `src/workflows/interceptors.ts`: sandbox interceptors that forward trace context to activities.
- `src/activities/index.ts`: the four activities, including the deliberate first-attempt failure.
- `src/activities/rules.ts`: eligibility, budget and decision logic.
- `src/activities/summary.ts`: the OpenAI call and the `llm` span wrapper.
- `src/tracing.ts`: OTLP exporter pointed at Opik, shared by both processes.
- `src/applications.ts`, `src/types.ts`, `src/env.ts`: fictional data, shared types, `.env` loading.
- `tests/`: vitest suites for the rules and for the summary wrapper running with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
