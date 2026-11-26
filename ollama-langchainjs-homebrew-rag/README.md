# ollama-langchainjs-homebrew-rag

**A handbook chatbot for a homebrew club that never phones a cloud model, with every step still visible in Opik.**

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)
![LangChain.js](https://img.shields.io/badge/LangChain.js-1.x-1C3C3C)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A1b-grey)
![Opik](https://img.shields.io/badge/Opik-2.3.5-2f54eb)

Running models on your own machine solves the privacy question and creates a debugging one: a 1B-parameter model gets answers wrong far more often than a frontier model, and without traces you cannot tell whether it was handed the wrong paragraph or ignored the right one. This example answers questions from the handbook of the Copperkettle Brewers, a made-up homebrew club, using only local models, and logs each question to Opik as a trace you can open and read.

## What you'll build

A small LangChain.js pipeline in TypeScript:

- `docs/` holds four short handbook files (recipes, sanitation rules, fermentation temperatures, equipment lending), 12 sections in all.
- `nomic-embed-text` embeds each section; a tiny in-memory retriever returns the top `K = 2` by cosine similarity.
- `llama3.2:1b` answers from those two sections, both served by Ollama.
- `opik-langchain`'s `OpikCallbackHandler` is passed to each call, so one question is one trace.

No OpenAI or Anthropic key is read anywhere; the demo works with those variables unset.

## See it in Opik

Open the project **ollama-langchainjs-homebrew-rag**. The demo asks three questions, so the Traces tab shows three traces, each named `ask_the_handbook`, with the question as input and the answer as output.

Open one and you see six spans: the root `ask_the_handbook`, then `RunnableLambda`, **`search_handbook`**, `ChatPromptTemplate`, **`ChatOllama`** and `StrOutputParser`. Two matter most:

- `search_handbook` (type `tool`) has the question as its query and the two retrieved sections as output. For the lager question it fetched "Lager Fermentation Range" plus "Cider Fermentation Range".
- `ChatOllama` (type `llm`) shows the assembled prompt, the answer, model `llama3.2:1b`, provider `ollama`, and token counts (219, 202 and 222 total tokens for the three questions in the run we checked).

That pair explains the one wrong answer in the demo. Asked how long a lager rests at 16 C, the model replies "The text does not specify the exact duration", yet `search_handbook` had fetched the section that says two days. Retrieval was fine; the small model missed it. The other two questions (the 40 euro kettle deposit, and not rinsing sanitiser) come back correct. Cost stays empty: Opik has no price for a local model, so the trace shows tokens but no dollars.

## Run it yourself

1. Install Ollama natively (https://ollama.com) or run it in Docker, then pull the two models:
   ```bash
   ollama pull llama3.2:1b
   ollama pull nomic-embed-text
   ```
   For Docker: `docker run -d -p 11434:11434 -v ollama:/root/.ollama ollama/ollama`, then `docker exec <container> ollama pull ...` for each model.
2. Start a local Opik (`./opik.sh` in the Opik repo) or use Opik Cloud.
3. Install and configure:
   ```bash
   npm install
   cp .env.example .env     # Opik URL, workspace, project, OLLAMA_BASE_URL
   ```
4. Run:
   ```bash
   npm run demo
   ```
   It takes about 10 seconds on a laptop CPU. Offline tests: `npm test` (they need no Ollama, no Opik and no keys; `OPIK_TRACK_DISABLE=true` turns the SDK's `track()` wrapper into a pass-through).

## Poke around

- Change `K` in `src/rag.ts` to 1 and watch `search_handbook` return a single section. Does the lager answer change?
- Ask something the handbook does not cover and read the `ChatOllama` prompt to see what the model was given.
- Swap `CHAT_MODEL` for a larger Ollama model and compare the lager trace.
- Point `OLLAMA_BASE_URL` at another machine on your network; traces look the same.

## Gotchas we hit

**The trace has no retrieval span.** Symptom: you see `RunnableLambda`, `ChatPromptTemplate` and `ChatOllama`, but nothing for the retriever. Cause: `OpikCallbackHandler` does log retriever runs (calling `retriever.invoke(q, { callbacks: [handler] })` directly gives a `tool` span), but a retriever called with no config inside a `RunnableLambda` never receives the handler. The fix is a named retrieval step that forwards the config:

```ts
const searchHandbook = async (question: string, config?: RunnableConfig) =>
  formatContext(await retriever.invoke(question, { ...config, runName: "search_handbook" }));
```

Wrapping the retrieval in the SDK's `track({ name: "search_handbook", type: "tool" }, ...)` instead does not help here: it creates a second, separate trace rather than a span inside the chain's trace.

**`npm install` fails with ERESOLVE on `opik-langchain`.** Cause: it declares a peer dependency on `opik@^1.8.75`, which excludes `2.3.5`. Fix, in `package.json`:

```json
"overrides": { "opik-langchain": { "opik": "$opik" } }
```

**The `ChatOllama` span has tokens but no cost.** The Ollama model reports usage to the JS handler, but Opik prices only known hosted models, so cost is not computed for `llama3.2:1b`. That is expected; the lesson here is tracing, not spend.

## How it's put together

- `src/main.ts` loads the nearest `.env`, creates the Opik handler, asks three questions and flushes.
- `src/rag.ts` holds the prompt, the model names, `K`, and the chain with the named `search_handbook` step.
- `src/handbook.ts` splits the docs into sections and provides the cosine-similarity retriever.
- `src/env.ts` walks up from the project folder to the first `.env`.
- `docs/` is the fictional club handbook.
- `tests/handbook.test.ts` covers chunking and ranking; `tests/tracing.test.ts` runs the chain with a stub model, a stub Opik client and a `track()` wrapper with tracking disabled.

*built with Opik · inspired by Opik's examples and documentation*
