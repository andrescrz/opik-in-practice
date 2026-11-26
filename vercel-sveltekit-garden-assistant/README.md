# vercel-sveltekit-garden-assistant

*A streaming garden chat in SvelteKit where every reply becomes an Opik trace and gets graded by a rule you never call from code.*

![TypeScript](https://img.shields.io/badge/typescript-5.6%2B-3178C6?style=flat&logo=typescript&logoColor=white)
![SvelteKit](https://img.shields.io/badge/sveltekit-2-FF3E00?style=flat&logo=svelte&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.3-2f54eb?style=flat)

Streaming makes chat feel fast and makes it awkward to observe: the answer is never a return value, every request re-sends the whole history, and "was that reply any good?" is a question nobody asks until a user complains. This example puts a small gardening assistant, Sprout, behind a SvelteKit streaming endpoint, wires it to Opik with one OpenTelemetry exporter, and adds a live online-evaluation rule so every chat turn is scored without a line of scoring code in the app.

## What you'll build

- A SvelteKit app with one page (the `Chat` class from `@ai-sdk/svelte`, which replaces the `useChat` hook you may know from React) and one streaming route, `POST /api/chat`, calling `streamText` on `gpt-4o-mini`.
- Six fictional plot notes in `data/` for the made-up Fernwick Vale community garden (planting calendar, tomatoes, basil, pest ID, watering, soil). The route picks the best two by keyword overlap and puts them in the system prompt.
- `src/lib/server/telemetry.ts`: a Node OpenTelemetry SDK holding `OpikExporter`, plus AI SDK v7's explicit `registerTelemetry(new OpenTelemetry(...))`. In v7 no spans exist until you call it.
- `scripts/opik-rest.mjs`: creates the Opik project and an LLM-as-judge rule named `answer_relevance` (gpt-4o-mini, sampling rate 100%), idempotently.
- `npm run demo`: ensures the rule, boots the dev server, plays three scripted multi-turn chats (7 turns), shuts the server down, then polls Opik until every trace carries its score.

## See it in Opik

Open the `vercel-sveltekit-garden-assistant` project. In the verified run it held 14 traces: 7 named `garden-chat-turn` (one per streamed reply) and 7 named `online_evaluation` (the judge's own runs, recorded by Opik).

Open a `garden-chat-turn` trace. It has two spans: a `general` span `step 1` wrapping an `llm` span `chat gpt-4o-mini`. The model resolves to `gpt-4o-mini-2024-07-18`, and the usage and cost columns are filled even though the reply streamed out: about 460 to 610 prompt tokens, 45 to 72 completion tokens and roughly $0.0001 per turn. The input shows the system prompt with the retrieved plot notes plus the whole conversation so far, which is why prompt tokens climb turn by turn.

The Threads tab shows 3 threads, with 3, 2 and 2 turns: tomatoes and blight, aphids on the beans, basil in the cold. The chat id sent by the client is the thread id.

In the trace table, the Feedback scores column shows `answer_relevance = 1` on all 7 chat traces, with the judge's reason stored on each score (for example "directly addresses the gardener's question about managing aphids without harsh chemicals"). In the project's online-evaluation rules there is exactly one rule, enabled, sampling 100%, no matter how many times you have run the demo.

## Run it yourself

1. In Opik, store your OpenAI key under Configuration, AI Providers. The judge runs inside the Opik server and cannot see your `.env`.
2. `cp .env.example .env`, add `OPENAI_API_KEY`, and point `OPIK_URL_OVERRIDE` at your Opik (a root-level `.env` further up the tree also works).
3. `npm install`
4. `npm run demo`. It takes about half a minute and prints each streamed reply, then a table of traces with their `answer_relevance` scores.
5. Or `npm run dev` and chat at http://localhost:5173 yourself (Vite's default port; the demo uses 4173).

To re-run cleanly, delete the earlier traces in the Opik UI, but leave the rule alone: it must exist before traffic arrives, and the demo re-creates it only if it is missing.

## Poke around

- Ask Sprout something the notes do not cover ("how do I prune an apple tree?") in `npm run dev` and see whether `answer_relevance` rewards an honest "I don't know".
- Edit the rule's prompt in the UI to also demand that the reply cite a plot note, then re-run and watch scores drop.
- Lower the sampling rate to 0.5 and count how many traces get scored.
- Swap the model in `src/routes/api/chat/+server.ts` for `gpt-4.1-mini` and compare per-turn cost in the traces table.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-vercel`.** `opik-vercel` declares a peer on the 1.x `opik` line, but npm's `latest` tag now points at 2.x. Pin `"opik": "^1.11.14"` (as `package.json` does) instead of letting it float. Using `legacy-peer-deps` instead also silences it, but then npm stops installing `zod`, and the dev server dies with `Could not resolve "zod/v4"` until you add `zod` yourself.

**Every trace is named `invoke_agent gpt-4o-mini`.** In AI SDK v7 the name passed to `OpikExporter.getSettings({ name })` does not reach the span. Pass it through `runtimeContext` (`traceName`), list it in `includeRuntimeContext`, and copy it in `enrichSpan` to `ai.telemetry.metadata.traceName`, exactly as `telemetry.ts` does. The thread id travels the same way via `ai.telemetry.metadata.threadId`.

**The judge gives some perfect answers a 0, and the reason says "both the input and output are null".** The first version of the rule used the whole `{{trace}}` as one variable. The model sometimes failed to find the question inside the serialised trace (2 of 7 scores were 0 on that run). Map `input` and `output` as separate variables and tell the judge what each contains, as `scripts/opik-rest.mjs` does; the next run scored 7 of 7.

**My trace table has twice as many rows as chats.** The judge's own runs are recorded in the same project as traces named `online_evaluation`. Filter on the name `garden-chat-turn` when counting your app's traffic.

**Scores stay empty.** Either the OpenAI key is not in Opik's provider store (the judge traces show an "API key not configured" error), or the rule was created after the traces arrived. Rules only score traces ingested while they are enabled.

## How it's put together

- `data/*.md` — six fictional plot notes (calendar, tomatoes, basil, pests, watering, soil).
- `src/lib/server/notes.ts` — loads notes, keyword retrieval, builds the system prompt.
- `src/lib/server/telemetry.ts` — Opik exporter, OTel SDK, `registerTelemetry`, flush on shutdown.
- `src/lib/server/env.ts` — walks up to the first `.env` before any Opik client exists.
- `src/hooks.server.ts` — imports the telemetry module once at server start.
- `src/routes/api/chat/+server.ts` — the streaming route with the trace name and thread id.
- `src/routes/+page.svelte` — the chat UI on `Chat` from `@ai-sdk/svelte`.
- `scripts/opik-rest.mjs` — project and idempotent online-evaluation rule, trace listing and deletion.
- `scripts/demo.mjs` — rule, server, scripted chats, shutdown, score polling.
- `tests/` — offline vitest tests for retrieval and the exporter settings. Run `OPIK_TRACK_DISABLE=true npm test`; no keys needed.

---

*built with Opik · inspired by Opik's examples and documentation*
