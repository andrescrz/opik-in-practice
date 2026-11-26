# openai-coworking-concierge

*A front-desk chatbot for a fictional coworking space, where every guest is a thread, every turn has a price tag, and the unhappy guest is one filter away.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-python-412991?style=flat&logo=openai&logoColor=white)
![Opik 2.3+](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)

Chatbots talk in conversations, but a provider dashboard only shows requests. When a guest asks three questions at the front desk, you get three unrelated rows, no idea what the guest cost you, and no idea whether they left satisfied. This example is the concierge for **Larkspur Yard**, an invented coworking space with hot desks, three meeting rooms and a list of house rules, and it uses Opik to put the conversation, the cost and the verdict back together.

## What you'll build

A small Python package (`concierge/`) plus a CLI, built on the plain OpenAI SDK with no agent framework. The space is described in a JSON file; a prompt module turns it into a system prompt; a `Session` keeps one guest's message history; a scripted demo plays three guests so nothing needs typing. Opik gets in with three small touches: `track_openai` wraps the client, `@opik.track` marks each turn as a trace carrying a `thread_id`, and one SDK call attaches a `guest-satisfaction` score after the run.

One of the three guests asks about bringing a dog and parking a van. Neither is in the facts, so the concierge honestly says "I don't know", and that guest is rated 0.0. That is the conversation you will go looking for in Opik.

## See it in Opik

Start the run, then open the project **`openai-coworking-concierge`**.

- **Traces tab.** 8 traces, all named `concierge-turn`. Expand one: it holds a single child span, `chat_completion_create` (type `llm`), with model `gpt-4o-mini-2024-07-18`, the full message array, and token usage. In the run I verified, the first turn of the hot-desk guest used 507 prompt and 68 completion tokens (about $0.000117); the guest's third turn re-sent 690 prompt tokens, because every call carries the whole history. Cost per turn is in the trace's cost column; across the 8 turns it stayed around $0.0001 each.
- **Threads tab.** 3 threads: `day-pass-hot-desk` (3 turns), `board-meeting-room` (3 turns) and `guest-with-dog` (2 turns). Open one to read it as a chat transcript.
- **Feedback scores.** The trace list has a `guest-satisfaction` column. It is set only on each conversation's last turn: 1.0 for the hot-desk and meeting-room guests, 0.0 for the dog guest, with the reason text on hover. Sort or filter on it to jump to the failed conversation, then check its trace: the model had no pet or parking facts, and admitted it instead of inventing a policy.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start Opik locally (or use Opik Cloud).
2. `cp .env.example .env`, add `OPENAI_API_KEY`, and adjust the Opik settings. A `.env` in any parent folder is found too.
3. `uv sync`
4. `uv run concierge` (about a minute, under a cent of API usage).
5. Open the `openai-coworking-concierge` project in Opik.

## Poke around

- `uv run concierge --chat` and talk to it; your session shows up as a new `chat-xxxxxxxx` thread.
- Add a `"pets"` rule to `concierge/data/space.json`, re-run, and watch the dog conversation change; update its rating in `concierge/demo.py` to match.
- Make the system prompt in `concierge/prompts.py` chattier (drop the three-sentence limit) and compare completion tokens and cost per turn.
- Change `MODEL` in `concierge/config.py` to `gpt-4.1-mini` and compare per-turn cost in the trace list.

## Gotchas we hit

**`AttributeError: 'NoneType' object has no attribute 'id'` in tests.** With `OPIK_TRACK_DISABLE=true`, a `@opik.track` function still runs but there is no current trace, so `opik_context.get_current_trace_data()` returns `None`. Guard it:

```python
trace = opik_context.get_current_trace_data()
self.last_trace_id = trace.id if trace else None
```

**Feedback scores are silently missing from the newest traces.** Traces are sent in the background; logging a score for a trace the server has not received yet has nothing to attach to. Call `opik.flush_tracker()` before `log_traces_feedback_scores(...)` (done in `concierge/feedback.py`).

**Traces land in the wrong project.** `OPIK_PROJECT_NAME` is read when the first Opik client is created, so set it before any traced call. `config.load_env()` does this right after loading `.env`.

## How it's put together

- `concierge/data/space.json` is the fictional Larkspur Yard: hours, desk types, rooms, booking terms, house rules.
- `concierge/config.py` loads `.env`, pins the Opik project, and builds the `track_openai`-wrapped client.
- `concierge/knowledge.py` loads the JSON and renders it as prompt text.
- `concierge/prompts.py` builds the system prompt, including the "never guess" instruction.
- `concierge/session.py` holds one guest's history; its `ask` is the traced turn with the `thread_id`.
- `concierge/demo.py` has the three scripted guests and their ratings.
- `concierge/feedback.py` turns ratings into Opik feedback scores.
- `concierge/cli.py` is the entry point (`concierge`, `concierge --chat`) and flushes Opik on exit.
- `tests/test_concierge.py` has offline tests with a stub client: facts, prompt, history, a traced call with tracking disabled, and feedback payloads. Run `OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
