# beeai-zoo-care-triage

*What was that agent thinking when it paged the wrong keeper? A BeeAI ReAct agent for zoo animal-care requests, with every iteration, model call and tool call in Opik.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6?style=flat&logo=typescript&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.13-f5c518?style=flat)
![Opik](https://img.shields.io/badge/Opik-OTLP%20ingestion-2f54eb?style=flat)

At Marrow Creek Zoo (fictional), keepers radio in short reports: "giraffe off feed", "penguin pool filter alarm". A triage agent has to work out how urgent it is and who to call. It reads the animal's care record, checks the enclosure's maintenance log, and finds the right person on the roster. A ReAct agent decides each step by writing a thought, calling a tool, reading the result and looping, but `agent.run()` returns only the final text. When the answer is wrong ("call the bird keeper" when the real problem is the pool equipment), the text can't tell you whether the agent never looked something up or looked it up and ignored it. The trace can.

## What you'll build

- A BeeAI `ReActAgent` on `gpt-4o-mini` with three tools over the JSON files in `data/`: `lookup_roster`, `get_care_record` and `get_maintenance_log`. Nothing leaves your machine except the model call.
- `npm run demo` triages three reports: a giraffe that won't eat, a penguin-pool filter alarm, and a quiet red panda.
- `npm run capped` runs the penguin alarm again with the loop limited to 2 iterations, so you can see what an incomplete ReAct run looks like.
- Tracing in one file, `src/instrumentation.ts`: BeeAI's OpenInference instrumentation plus a protobuf OTLP exporter pointed at Opik. No Opik SDK is installed.

## See it in Opik

Open the **beeai-zoo-care-triage** project. After the two commands above there are 4 traces (the demo's three, then the capped one), all named `beeai-framework-main`, one per `agent.run()`. Open them oldest first:

- **Giraffe.** 73 spans and 5 `iteration-N` spans. `get_care_record` was called twice (the model re-asked once), then `get_maintenance_log` returned the open "browse feeder winch, cable fraying" item, which the final answer cites.
- **Penguins.** 57 spans, 4 iterations: care record, maintenance log (the open filter-bank items), roster, answer. Open the roster span: the agent asked for `birds` (Sunniva Holt), although the instructions say pool-equipment alarms go to `aquatics`. The routing slip is wrong because of the model's choice of tool argument, not because of the data.
- **Red panda.** 57 spans. Its care record says reduced *morning* activity is *not* normal. Across my runs the answer was sometimes "routine, quiet is normal" and sometimes "same-day"; compare the `get_care_record` result with the final answer to see whether the agent used what it read. Outputs vary run to run, and so do span counts by a few.
- **The capped run.** 34 spans, 2 iterations, and an error on the trace: the agent used its two iterations on the care record and maintenance log and was stopped before it reached the roster.

Under each root you will see the loop as nested spans: `iteration-N` groups the LLM spans (`backend.openai.chat.*`, type `llm`) and tool spans (`tool.dynamic.<name>.*`, type `general`; this instrumentation doesn't mark them as `tool`). The `success` span of a chat call carries the token usage. In my run the full demo used about 2,900 to 3,100 tokens per trace for roughly $0.0005 each (`gpt-4o-mini`).

## Run it yourself

1. Have Opik running (`./opik.sh` in the Opik repo gives you http://localhost:5173) or use Opik Cloud.
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. For Opik Cloud set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`, `OPIK_WORKSPACE` and `OPIK_API_KEY`.
3. `npm install`
4. `npm run demo`, then `npm run capped`.
5. Open the `beeai-zoo-care-triage` project in Opik. Spans take a few seconds to appear.

Offline tests (no keys, no Opik): `npm test`. They set `OTEL_SDK_DISABLED=true`, the standard OpenTelemetry switch that stops the SDK from starting.

## Poke around

- Add a `sea otter` report ("Pebble is matted and not grooming") and watch which enclosure's maintenance log the agent reads: the `kelp-tank` skimmer pump is open there.
- Rewrite instruction 4 in `src/agent.ts` to be vaguer and re-run the penguin request; compare the `lookup_roster` argument in the span.
- Pass `maxIterations: 3` in `src/capped.ts` and find the iteration at which the run now ends.
- Change `MODEL` in `src/config.ts` to another OpenAI chat model and check that the cost column still fills in.

## Gotchas we hit

**The agent runs fine but nothing appears in Opik.** The OpenInference BeeAI instrumentation only supports `beeai-framework` `>=0.1.9 <0.1.14`; with the latest release (0.1.32) it prints `DependencyConflict` and silently patches nothing. Pin the exact version: `"beeai-framework": "0.1.13"` (and `@arizeai/openinference-instrumentation-beeai` 1.6.2).

**Still no spans under `tsx`/ESM.** The framework is imported before the instrumentation's module hook can see it. Call `beeAI.manuallyInstrument(beeaiFramework)` right after `sdk.start()`, and import `instrumentation.ts` *before* `agent.ts`.

**`400 Cannot find field: schemaUrl`.** Opik rejects the OTLP/JSON exporter. Use `@opentelemetry/exporter-trace-otlp-proto`, with the project in the `projectName` header and the workspace in `Comet-Workspace`.

**Usage appears but cost is `null`.** The instrumentation puts the model name on the `start` span and token counts on the `success` span, and never reports a provider. Opik prices a span only when it holds usage, provider and model. A tiny span processor sets `gen_ai.system = "openai"` and `llm.model_name = "gpt-4o-mini"` on every `backend.openai.chat*` span when it starts. Not every `success` span carries usage, so only some LLM spans show a cost; the trace total sums them.

## How it's put together

- `src/instrumentation.ts`: OTel `NodeSDK`, BeeAI instrumentation, protobuf exporter, and the provider/model stamp for cost.
- `src/agent.ts`: triage instructions and the `ReActAgent`, with configurable iteration limits.
- `src/tools.ts`: the three BeeAI tools; `src/lookups.ts`: the plain functions behind them, and a check that the named person is on the roster.
- `src/config.ts`: model and provider ids shared by the agent and the tracing setup.
- `src/demo.ts`: three reports, flush at the end. `src/capped.ts`: the 2-iteration run.
- `data/`: fictional roster, care records and maintenance log.
- `tests/lookups.test.ts`: lookups, newest-first log, roster check. `tests/tracing-disabled.test.ts`: instrumented tools run with the OTel SDK disabled.

*built with Opik · inspired by Opik's examples and documentation*
