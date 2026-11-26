# voltagent-restaurant-reservations

![Node 20.19+](https://img.shields.io/badge/node-20.19%2B-339933?logo=node.js&logoColor=white)
![@voltagent/core 2.11.1](https://img.shields.io/badge/%40voltagent%2Fcore-2.11.1-1b1f23)
![Tests: vitest](https://img.shields.io/badge/tests-vitest-6e9f18)

**A VoltAgent booking host for a candle-lit restaurant, whose OpenTelemetry spans arrive in Opik with real token usage and cost.**

VoltAgent already emits OpenTelemetry spans, so pointing an OTLP exporter at Opik looks like the whole job. It isn't quite: send VoltAgent's spans as they are and Opik receives every one of them as a plain `general` span, with no model, no token counts and no cost. The data is there, under names Opik doesn't read (`llm.usage.prompt_tokens` instead of `gen_ai.usage.prompt_tokens`). This example shows the gap and closes it with a small exporter wrapper that renames the attributes on the way out.

## What you'll build

A reservation assistant for **Lantern & Fig**, a fictional restaurant with six tables (two 2-tops, two 4-tops, a 6-top and an 8-top) and a handful of existing bookings, all kept in `data/`. One VoltAgent `Agent` on `gpt-4o-mini` has four tools:

- `check_availability` — is a table free for this party at this date and time? If not, which nearby times are?
- `book_table` — create a reservation on the smallest free table that fits.
- `modify_booking` — move a booking or change its party size; the original stays untouched if the new slot is full.
- `cancel_booking` — remove a booking and free its table.

`npm run demo` plays one phone call in four turns: a party of four asks for 19:00 on 2026-12-12 (full, so the host offers 17:30, 18:00 and 18:30), books the earliest one for Dana Whitlock (`LF-1007`), moves Callum Reid's `LF-1006` to 19:30 for three people, and cancels `LF-1002`.

Tracing lives in one file, `src/observability.ts`: an OTLP/protobuf exporter aimed at Opik, wrapped by `GenAIMappingExporter`, which copies VoltAgent's attributes to the `gen_ai.*` names. No agent or tool file knows tracing exists.

## See it in Opik

Open the **voltagent-restaurant-reservations** project. After one clean run it holds **4 traces**, one per guest turn, each named `lantern-fig-host`. Open any of them and you will see three spans:

- `lantern-fig-host` — the agent run (type `general`), with the guest's sentence as input and the host's reply as output.
- `llm:generateText` — type **llm**, model `gpt-4o-mini`, provider `openai`, with prompt, completion and total tokens and an estimated cost. In my run the cancellation turn used 823 prompt + 44 completion tokens for about $0.00015, and the four turns together used 3,068 tokens for about $0.0005. The trace row in the table carries the summed usage and cost too.
- `tool.execution:check_availability` (or `book_table`, `modify_booking`, `cancel_booking`) — type **tool**, with the model's arguments as input (`{"booking_id":"LF-1002"}`) and the result as output (`{"ok": true, "cancelled": {...}}`).

That is the contrast worth looking at: the booking turn's tool span tells you which table the system picked, and the llm span tells you what the turn cost.

To see the "before", run `OPIK_GENAI_MAPPING=off npm run demo` (delete the earlier traces first). The same four traces arrive, but every span is `general`, and usage and cost are empty.

## Run it yourself

1. Start Opik locally (or have an Opik Cloud account) and `cd voltagent-restaurant-reservations`.
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. For Opik Cloud also set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`, `OPIK_API_KEY` and `OPIK_WORKSPACE`. (A `.env` in a parent folder is picked up as well.)
3. `npm install`
4. `npm run demo` — about 15-25 seconds, well under a cent.
5. Open the project in Opik and click the newest trace.

Tests need no keys and no Opik: `npm test` (tsc check: `npm run typecheck`).

## Poke around

- Ask for a party of 9 and watch `check_availability` return `available: false` with no alternatives: no table seats nine.
- Read `providerFor` in `src/observability.ts`: the provider is guessed from the model name, so a new model family needs one line there before its cost can be priced.
- Remove the `delete attrs["input"]` line in `mapToGenAI` and compare the tool span's input in Opik.
- Add a turn asking to move `LF-1001` to 8 people: `modify_booking` returns an error, the booking keeps its original 4 seats, and the span shows exactly why.

## Gotchas we hit

**Every span is `general`, and usage and cost are empty.** VoltAgent names its attributes `span.type`, `llm.model` and `llm.usage.*`; Opik reads `gen_ai.*`. Add the standard names before export:

```ts
attrs["gen_ai.request.model"] = attrs["llm.model"];
attrs["gen_ai.provider.name"] = "openai"; // Opik prices a span from provider + model
attrs["gen_ai.usage.prompt_tokens"] = attrs["llm.usage.prompt_tokens"]; // likewise completion_ and total_
```

For tool spans, rename `input` to `gen_ai.tool.call.arguments`.

**The `llm:generateText` span has no output.** VoltAgent puts the completion on the agent span, not the llm span, so Opik shows the reply under `lantern-fig-host`. The mapping doesn't invent an output.

**The host forgets the date between turns (it booked "October 9th").** `generateText(string)` is stateless, so "that evening" has nothing to refer to. The demo passes the running `history` array as the messages instead; each turn is still its own trace.

**OTLP must be protobuf.** `@opentelemetry/exporter-trace-otlp-proto` is used on purpose; Opik's OTLP endpoint rejects the JSON exporter (`400 Cannot find field: schemaUrl`). The project comes from the `projectName` header and the workspace from `Comet-Workspace`.

## How it's put together

- `data/restaurant.json` — tables, opening hours, seating length.
- `data/bookings.json` — the starting bookings.
- `src/reservations.ts` — the in-memory booking book: overlap check, alternatives, book/modify/cancel.
- `src/tools.ts` — the four VoltAgent tools over a `ReservationBook`.
- `src/agent.ts` — the host agent: instructions, model, tools.
- `src/observability.ts` — OTLP exporter for Opik plus the `gen_ai.*` mapping (the only Opik code).
- `src/demo.ts` — loads `.env`, registers observability, plays the four turns, flushes.
- `tests/reservations.test.ts` — booking logic: alternatives, smallest table, double-booking, modify, cancel.
- `tests/tools-and-mapping.test.ts` — a tool run with no tracing registered, and the attribute mapping.

---

*built with Opik · inspired by Opik's examples and documentation*
