# opik in practice

**24 small, runnable LLM apps, each built to show one thing [Opik](https://github.com/comet-ml/opik) can tell you about your app.**

![examples](https://img.shields.io/badge/examples-24-informational) ![python](https://img.shields.io/badge/Python-15-3776AB) ![typescript](https://img.shields.io/badge/TypeScript-7-3178C6) ![low-code](https://img.shields.io/badge/low--code-2-orange) ![license](https://img.shields.io/badge/license-Apache--2.0-green)

Every folder is a complete app with fictional data, a fictional business and a real failure or comparison worth
looking at: a retriever that pulled the right page and a model that ignored it, a prompt that goes from 0/6 to
6/6, an agent that paged the wrong keeper, a transcript that misspelled a pet owner's name. Most run in a minute or
two for a few cents (one runs entirely on a local model and costs nothing). Each README tells you which trace,
span, thread or experiment to open in Opik and what you'll find there.

## Pick an example by what you want to learn

### Follow a request through your app

| Example | Stack | What it shows |
|---|---|---|
| [openai-coworking-concierge](openai-coworking-concierge) | Python · OpenAI SDK | Threads per guest, cost per turn, a satisfaction score logged after the chat |
| [langchain-fastapi-library-recs](langchain-fastapi-library-recs) | Python · LangChain + FastAPI | String-in/string-out root runs, so the Threads view reads like a transcript |
| [vercel-sveltekit-garden-assistant](vercel-sveltekit-garden-assistant) | TypeScript · Vercel AI SDK + SvelteKit | Streaming spans, threads, and an online LLM-judge rule scoring every reply |
| [temporal-ts-grant-review](temporal-ts-grant-review) | TypeScript · Temporal | One trace across two OS processes, with a failed-then-retried activity |
| [opik-py-redaction-pipeline](opik-py-redaction-pipeline) | Python · Opik SDK only | Hand-built spans (tool, llm, guardrail), manual usage, feedback scores, flush behaviour |
| [ollama-langchainjs-homebrew-rag](ollama-langchainjs-homebrew-rag) | TypeScript · LangChain.js + Ollama | Full tracing with zero cloud calls, and making a hidden retriever step visible |

### Agents: who called which tool, and what it cost

| Example | Stack | What it shows |
|---|---|---|
| [openai-agents-insurance-claims](openai-agents-insurance-claims) | Python · OpenAI Agents SDK | Triage-to-specialist handoffs and tool calls as a span tree, threads via group_id |
| [crewai-home-renovation-planner](crewai-home-renovation-planner) | Python · CrewAI | One trace per kickoff, tokens and dollars per agent |
| [langgraph-postmortem-team](langgraph-postmortem-team) | Python · LangGraph | A planner, investigator loop and writer graph, with cost per node |
| [mastra-banking-agent](mastra-banking-agent) | TypeScript · Mastra (OTel) | Agent loops with real `execute_tool` spans: balance, transactions, card freeze |
| [voltagent-restaurant-reservations](voltagent-restaurant-reservations) | TypeScript · VoltAgent (OTel) | Mapping OTel attributes to `gen_ai.*` so usage and cost actually land |
| [beeai-zoo-care-triage](beeai-zoo-care-triage) | TypeScript · BeeAI (OpenInference) | ReAct iterations, LLM and tool spans, and an agent that runs out of iterations |
| [smolagents-solar-energy-analyst](smolagents-solar-energy-analyst) | Python · smolagents (OpenInference) | The pandas code the agent wrote, and its execution logs, inside the spans |

### Measure quality: datasets, experiments, test suites

| Example | Stack | What it shows |
|---|---|---|
| [langgraph-national-parks-rag](langgraph-national-parks-rag) | Python · LangChain + LangGraph | Two retrieval settings as experiments, scored for hallucination and context precision |
| [llamaindex-syllabus-qa](llamaindex-syllabus-qa) | Python · LlamaIndex | Retrieval and synthesis spans, and a section-tagged test suite with honest failures |
| [openai-shipping-label-extraction](openai-shipping-label-extraction) | Python · OpenAI vision | Label images attached to traces, and a suite that catches smudged fields |
| [whisper-vet-voicemail-triage](whisper-vet-voicemail-triage) | Python · OpenAI TTS + Whisper | A playable MP3 on every trace, and a judge suite run three times per item |
| [dspy-board-game-rules-qa](dspy-board-game-rules-qa) | Python · DSPy | The same suite before and after compiling: 0/8 → 6/8 |
| [litellm-code-review-router](litellm-code-review-router) | Python · LiteLLM | The same prompts on OpenAI and Anthropic, with cost and latency side by side |

### Manage prompts

| Example | Stack | What it shows |
|---|---|---|
| [opik-ts-podcast-title-prompts](opik-ts-podcast-title-prompts) | TypeScript · Opik TS SDK | Two immutable prompt versions with a diff, and a suite that goes 0% → 100% |
| [openai-py-storybook-illustrations](openai-py-storybook-illustrations) | Python · OpenAI images | A versioned illustration brief, and each generated PNG attached to its trace |
| [optimizer-app-review-classifier](optimizer-app-review-classifier) | Python · Opik Agent Optimizer | A score curve across optimization trials, with the winner saved to the prompt library |

### Apps with no code to instrument

| Example | Stack | What it shows |
|---|---|---|
| [n8n-food-bank-volunteer-screening](n8n-food-bank-volunteer-screening) | n8n in Docker | A span per workflow node via lifecycle hooks; the workflow itself is untouched |
| [dify-gym-assistant](dify-gym-assistant) | Dify in Docker | Dify's built-in Opik integration, switched on through its API |

## Running one

1. **Opik.** Self-host it (see the [Opik docs](https://www.comet.com/docs/opik/)) and it will be on `http://localhost:5173` with no API key, or use Opik Cloud and set `OPIK_URL_OVERRIDE` and `OPIK_API_KEY`.
2. **Keys.** Run `cp .env.example .env` at the repo root and add `OPENAI_API_KEY` (plus `ANTHROPIC_API_KEY` for the LiteLLM router). Examples find this file by walking up from their folder.
3. **Run.** Follow the example's README. Python examples use [uv](https://docs.astral.sh/uv/) (`uv run ...`), TypeScript ones use `npm install && npm run demo`, and the n8n and Dify ones use `./setup.sh` and a demo script.
4. **Look.** Open the Opik project named exactly like the folder.

Python and TypeScript examples also ship offline tests that need no keys and no Opik server (`uv run pytest` or
`npm test`), so you can see that tracing doesn't get in the way of unit tests.

## What every folder contains

- `README.md`: the problem, what to open in Opik, how to run it, a few experiments to try, and the gotchas we actually hit.
- `.env.example`: the variables that example reads, with links to where to get them.
- The app, its fictional data (`data/` or `docs/`), and its tests.

Every place the code touches Opik (wrapping a client, opening a span, logging usage, attaching a file, creating
a dataset) has a short comment saying what it produces in Opik and what breaks without it.

## License

[Apache 2.0](LICENSE)

---

*inspired by [Opik](https://github.com/comet-ml/opik)'s examples and [documentation](https://www.comet.com/docs/opik/)*
