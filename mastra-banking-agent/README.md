# mastra-banking-agent

![Node](https://img.shields.io/badge/node-22.13%2B-339933?logo=node.js&logoColor=white)
![Mastra](https://img.shields.io/badge/mastra-core%201.86-0b0b0b)
![Opik](https://img.shields.io/badge/Opik-OpenTelemetry-2f54eb)

**A credit-union banking assistant built on Mastra, where every balance lookup and card freeze shows up as its own tool span in Opik.**

When a banking assistant freezes the wrong card, "the chat looked fine" is not an answer. You need to know which account id the model typed into the tool, what the core system returned, and whether the freeze ran before or after the member asked for it. This example wires a Mastra agent to Opik through OpenTelemetry so each `agent.generate()` call becomes a trace tree you can read step by step.

## What you'll build

An assistant for Harbor Pines Credit Union (entirely fictional) running on `gpt-4o-mini`, with three tools over JSON files in `data/`:

- `get_balance` returns an account balance plus the member's cards
- `get_recent_transactions` returns the latest activity, newest first
- `freeze_card` flips a card to `frozen` in memory

Tracing lives in one file, `src/mastra.ts`: Mastra's `Observability` layer with an `OtelExporter` aimed at Opik's OTLP endpoint. The agent and tool code never mention tracing. `npm run demo` plays three members: a balance check, a transaction review, and a fraud report that ends in a card freeze.

## See it in Opik

Open the `mastra-banking-agent` project and go to **Traces**. After one run there are three traces named `invoke_agent harbor-pines-assistant`.

Open the third one (Declan reporting two Lisbon ATM withdrawals). It has 29 spans: an `invoke_agent` root, four `agent_step` spans, four `chat` spans of type `llm` (model `gpt-4o-mini-2024-07-18`, provider `openai`), and three `execute_tool` spans of type `tool`. Click each:

- `execute_tool getBalance` input: `{"account_id": "CHK-3318-01"}`, with the balance and card list as output
- `execute_tool getRecentTransactions`: `limit: 5` and the two $200 Lisbon rows in the result
- `execute_tool freezeCard`: `{"card_id": "CARD-4402"}` returning `{"status": "frozen"}`

The model got that card id from the earlier `getBalance` result, not from the member's message, and you can see it in the spans. The first two traces are shorter (15 spans, one tool call each). Token usage lands on every `chat` span (the Declan trace totals 2,074 tokens), and Opik prices it: about $0.00037 for that trace, because the provider arrives as `openai`.

The span tree also includes `processor_run` and `model_chunk` spans, which are Mastra internals; collapse them to read the tool story.

## Run it yourself

1. Start Opik (local: `./opik.sh` from the Opik repo, or use Opik Cloud).
2. `cp .env.example .env` and set `OPENAI_API_KEY`. For a local Opik also set `OPIK_URL_OVERRIDE=http://localhost:5173/api` and `OPIK_WORKSPACE=default`. For Opik Cloud use `https://www.comet.com/opik/api`, your workspace name, and `OPIK_API_KEY`. A `.env` in a parent folder is found too.
3. `npm install`
4. `npm run demo` (about 20 seconds, a fraction of a cent)
5. Open the project in Opik.

Offline tests: `npm test` (no keys, no Opik needed).

## Poke around

- Change request 3 so Declan only asks "is my card safe?" and check that no `execute_tool freezeCard` span appears.
- Ask about `CHK-9999`; the tool span returns `{"error": ...}` and you can watch how the model words it.
- Set `maxSteps: 1` in `src/demo.ts` and see the loop stop after the first tool call.
- Rename the project with `OPIK_PROJECT_NAME` and watch a new project appear.

## Gotchas we hit

**Nothing shows up, and the project is never created.** The default `protocol: "http/json"` posts a payload that Opik answers with `400 Invalid JSON message ... Cannot find field: schemaUrl in message ... Resource`. The exporter swallows it quietly. Set `protocol: "http/protobuf"` in the `custom` provider config (the protobuf exporter ships as a dependency of `@mastra/otel-exporter`).

**The trace's Output column is empty.** Mastra's span mapping puts the agent's reply in span attributes, not in the field Opik reads as trace output, so the trace list shows an input but no output. The answer is still visible: open the `invoke_agent` root or the last `chat` span. This example does not add a mapper.

## How it's put together

- `src/mastra.ts`: the Mastra instance and the Opik OTLP exporter
- `src/agent.ts`: the assistant's instructions, model and tools
- `src/tools.ts`: the three Mastra tools
- `src/bank.ts`: loads `data/` and holds the in-memory card state
- `src/env.ts`: finds the nearest `.env` walking up the folders
- `src/demo.ts`: the three scripted requests and the exporter flush
- `data/members.json`, `data/transactions.json`: fictional members and activity
- `tests/tools.test.ts`: tool behaviour offline; `tests/wiring.test.ts`: the traced Mastra instance builds with no Opik reachable

---

*built with Opik · inspired by Opik's examples and documentation*
