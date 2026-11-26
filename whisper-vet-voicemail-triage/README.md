# whisper-vet-voicemail-triage

**A voicemail you can press play on, attached to the trace that triaged it.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat)](https://docs.astral.sh/uv/)

When a clinic's after-hours voicemail gets mis-sorted, the log only holds a transcript, and the transcript is already a guess. Speech-to-text turns "Oyelaran" into "Oilaren" and the model sorts the call based on that guess. If a poisoned dog ends up at the bottom of the callback list, you want to hear the original message, not read the pipeline's account of it. This example triages five fictional voicemails for a made-up vet clinic and keeps the audio next to every decision.

## What you'll build

A four-step pipeline on the OpenAI Python SDK, one Opik trace per voicemail:

1. **Synthesize.** The scripts in `data/voicemails.json` are spoken by `tts-1`, one voice per caller, into `audio/` (git-ignored, regenerated every run; about 200-300 KB each).
2. **Transcribe** with `whisper-1`.
3. **Triage** with `gpt-4o-mini`: caller, pet, phone, urgency (`emergency`, `urgent`, `routine`) and a one-sentence reason.
4. **Callback list**, sorted most urgent first.

Plus `evaluate.py`, an Opik test suite where an LLM judge checks each triage result, with an execution policy of three runs per item to absorb noise.

One script is deliberately tricky: the rabbit owner apologises ("probably nothing, sorry to bother you") while describing a rabbit that has stopped eating and passing droppings, which is an emergency.

## See it in Opik

Open the **whisper-vet-voicemail-triage** project. After `main.py` there are five `triage-voicemail` traces. Open one and you'll see this tree:

- `triage-voicemail` (root, input is the voicemail script)
  - `synthesize-voicemail` containing an `audio.speech.create` span of type `llm`, with the character count as usage and an estimated cost of roughly $0.003 to $0.005
  - `transcribe` (a general span; its output is the transcript)
  - `triage` containing `chat_completion_create` (llm, about 300 prompt and 60 completion tokens, cost near $0.00008)

On the trace's Attachments tab sits the MP3, e.g. `clover-not-eating.mp3`, with an audio player. Listen, then compare with the `transcribe` output. In the verified run Whisper heard "Marcus Oilaren" and "Dana Whitcomb" for "Marcus Oyelaran" and "Dana Whitcombe", so the callback list carries the misspelled names. The numbers came back fine. Whisper calls are not wrapped by `track_openai`, so `transcribe` is a plain span without cost or token counts.

Run `evaluate.py` and open the **Test suites** tab, suite `whisper-vet-voicemail-triage-suite`. The latest run covered 5 items x 3 runs: every item passed, 100% on both global assertions (name and phone come from the transcript; the reason invents nothing) and 3/3 on each per-voicemail urgency assertion. The same project also gains 15 `evaluation_task` traces, one per run.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/). Copy `.env.example` to `.env` (here or in any parent folder) and set `OPENAI_API_KEY`. The defaults point at a local Opik on `localhost:5173`; for Opik Cloud set `OPIK_URL_OVERRIDE=https://www.comet.com/opik/api`, `OPIK_API_KEY` and `OPIK_WORKSPACE`.
2. `uv sync`
3. `uv run main.py` (about two minutes, a few cents: five TTS calls, five transcriptions, five completions)
4. `uv run evaluate.py` (about 15 seconds; replays the transcripts written to `out/`)
5. Open the project in Opik, pick a trace, then Attachments, and press play.

Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Edit a script in `data/voicemails.json`, for instance make the dog owner mumble or add background chatter words, and see how the transcript and urgency change.
- Delete the sentence "Judge by the symptoms, not by the caller's tone" from `TRIAGE_SYSTEM_PROMPT` and rerun both scripts. Watch the rabbit item's assertion.
- Change `runs_per_item` to 1 in `evaluate.py` and rerun a few times to see whether the suite verdict wobbles; with 3 and a threshold of 2, a single bad judge call can't flip an item.
- Swap `TTS_MODEL` for `gpt-4o-mini-tts` or `TRANSCRIBE_MODEL` for `gpt-4o-mini-transcribe` and compare name spellings.

## Gotchas we hit

- **`transcribe` shows no cost or tokens.** `track_openai` instruments chat and speech calls, but the Whisper transcription is only recorded as the span that wraps it (a plain `@opik.track`). Put whatever you want to see (transcript, duration) in that span's output; don't expect usage.
- **Traces land in "Default Project".** Opik reads the project name when it first initialises, so `main.py` loads `.env` and sets `OPIK_PROJECT_NAME` before `import opik`. Keep that order if you restructure imports. Suites also need `project_name=` in `get_or_create_test_suite`, otherwise the experiment goes to the default project.
- **Judge model overrides.** If you pass a custom judge model to `run_tests`, don't include `reasoning_effort`; the judge call fails. The default judge works, and flakiness is handled with `global_execution_policy={"runs_per_item": 3, "pass_threshold": 2}`.
- **Whisper misspells names.** Not an error, so nothing flags it. That is why the audio is attached: the only way to catch it is to listen.

## How it's put together

- `main.py`: the pipeline, tracing, attachment and callback-list sorting.
- `data/voicemails.json`: the five fictional voicemail scripts with a TTS voice each.
- `evaluate.py`: the test suite with global and per-item assertions and the execution policy.
- `tests/test_triage.py`: offline tests (parsing, sorting, fixtures, a traced function with a stubbed client).
- `pyproject.toml`, `.env.example`, `.gitignore`: dependencies, settings, and the ignored `audio/` and `out/` outputs.

---

*built with Opik · inspired by Opik's examples and documentation*
