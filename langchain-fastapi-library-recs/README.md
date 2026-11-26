# Alder Creek Library Chat

**`langchain-fastapi-library-recs`** — a book-recommendation chat on FastAPI whose Opik Threads tab reads like a reference-desk transcript.

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/langchain--core-1.x-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/opik-2.3.5-2f54eb?style=flat)

---

A chat endpoint is stateless from the outside: each `POST /chat` is one request, and a patron who asks four follow-up questions leaves four unrelated rows in your tracing backend. To answer "why did it recommend a book that was checked out?" you need the whole conversation, in order, in words a librarian can read, not a pile of JSON.

This example is the backend for a reading assistant at the Alder Creek Branch Library, an invented library with a 25-book catalog in `data/catalog.json`. Patrons describe what they like ("quiet mysteries by the sea"), the assistant recommends from the catalog only, and follow-ups such as "something shorter" or "is that one on the shelf?" work because each session remembers its earlier turns.

## What you'll build

- `librarian/catalog.py`: loads the catalog and ranks books by keyword overlap. Curated tags and genre count double against summary words. No embeddings, no network.
- `librarian/chat.py`: one LangChain chain, `load-turn-context -> prompt -> gpt-4o-mini -> StrOutputParser`. It takes the patron's message as a string and returns the reply as a string. The first step pulls session history and catalog matches, so nothing structured has to ride in the chain's input.
- `librarian/app.py`: the FastAPI app, `POST /chat {message, session_id} -> {reply}`. Each request creates an `OpikTracer(thread_id=session_id)`.
- `main.py`: boots the app in-process with FastAPI's `TestClient`, plays three scripted conversations (8 turns in total), flushes, and exits. No server is left running.

## See it in Opik

Open the `langchain-fastapi-library-recs` project after a run.

**Threads tab.** Three threads: `patron-cozy-coastal` (3 turns), `patron-teen-sci-fi` (3 turns) and `patron-travel-nonfiction` (2 turns). Open one and each turn is the patron's sentence followed by the assistant's reply. A thread is built from the root input and output of its traces, and here those are the plain strings (`{'input': 'Something shorter, with a bit of a puzzle in it.'}` and the reply text), because the chain takes and returns a string. History and catalog matches are loaded inside the chain, so they never show up in the root input.

**Traces tab.** 8 traces, all named `library-chat-turn`, each with `thread_id` set to the session id. Open one: it has 5 spans. `load-turn-context` (general) contains `search-library-catalog` (tool), so you can see the query that was run and the exact catalog lines that came back, including the "all copies out; holds open" tag the model is told to mention. Next to it sit `ChatPromptTemplate`, `ChatOpenAI` (llm) and `StrOutputParser`. The `ChatOpenAI` span has prompt and completion token counts (333 to 457 total tokens per turn in this run) and an estimated cost; the whole 8-turn run came to about $0.0008.

Click through the three-turn `patron-cozy-coastal` thread and compare the `ChatOpenAI` input on turn 3 with turn 1: the earlier exchanges are in the prompt, and the catalog matches for turn 3 were searched using the earlier patron messages too.

## Run it yourself

1. `cd langchain-fastapi-library-recs`
2. `cp .env.example .env` and add `OPENAI_API_KEY` (a `.env` in any parent folder also works). Defaults point at a local Opik on `http://localhost:5173/api/`; for Opik Cloud set `OPIK_API_KEY` and `OPIK_WORKSPACE` and remove `OPIK_URL_OVERRIDE`.
3. `uv run main.py` (about 30-40 s, a fraction of a cent of gpt-4o-mini).
4. Open the project in Opik and look at Threads, then Traces.

To use it as a real service: `uv run uvicorn librarian.app:app --port 8000`, then
`curl -s localhost:8000/chat -H 'content-type: application/json' -d '{"message":"cozy mysteries?","session_id":"me"}'`.

Offline tests (no keys, no Opik): `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change one `session_id` in `CONVERSATIONS` to reuse another's. The two scripts merge into a single thread, in order.
- Ask for something the catalog lacks ("a cookbook about fermentation"). Open the `search-library-catalog` span: it returns `(no catalog matches)`, and the model should ask a question rather than invent a book.
- Make the chain's root input richer (for example invoke it with a dict holding the message plus the history) and re-run: compare what the Threads view now shows per turn with the string-in version.
- Swap the model name in `build_chain` for another model and compare cost per trace.

## Gotchas we hit

**A LangChain retriever never shows up as a span.** Symptom: you build a `BaseRetriever`, put it in the chain, and the trace has the surrounding runnables but no retrieval step. Cause: with `opik 2.3.5` and `langchain-core 1.8`, `OpikTracer` does not record retriever runs; we ran `R() | RunnableLambda(...)` with a minimal retriever and only the lambda was logged. Fix: do the lookup in a plain function and decorate it, as `chat.py` does:

```python
@opik.track(name="search-library-catalog", type="tool")
def retrieve_books(query: str) -> str: ...
```

Called inside a runnable, the tracked function nests under that runnable's span (here `load-turn-context`).

## How it's put together

- `librarian/catalog.py`: catalog loading, keyword scoring, formatting of matches for the prompt.
- `librarian/chat.py`: system prompt, per-session memory, the tracked catalog lookup, the chain.
- `librarian/app.py`: FastAPI app, `.env` loading, project name, per-request `OpikTracer` with the thread id.
- `main.py`: scripted conversations through `TestClient`, then `opik.flush_tracker()`.
- `data/catalog.json`: the 25 fictional books.
- `tests/test_library.py`: catalog search and formatting, the traced function with tracking disabled, the endpoint with a fake chat model (string in, string out, memory per session), input validation.

---

*built with Opik · inspired by Opik's examples and documentation*
