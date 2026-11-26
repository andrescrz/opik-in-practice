"""Veterinary voicemail triage, traced with Opik.

Each scripted voicemail in data/voicemails.json becomes one trace in the
"whisper-vet-voicemail-triage" project:

    triage-voicemail                  <- whole pipeline, MP3 attached
    |- synthesize-voicemail           <- tts-1 text-to-speech, written to audio/
    |- transcribe                     <- whisper-1 speech-to-text
    '- triage                         <- gpt-4o-mini -> urgency + reason
       '- chat_completion_create      <- logged by track_openai (tokens, cost)

The audio is regenerated on every run (it is output, git-ignored), so the
repo only ships the small text scripts.
"""

import json
import os
from functools import cache
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = EXAMPLE_DIR / "audio"
OUT_DIR = EXAMPLE_DIR / "out"

# Load the first .env found walking up from this folder, and pin the Opik
# project, before opik is imported; otherwise traces land in "Default Project".
load_dotenv(find_dotenv())
os.environ["OPIK_PROJECT_NAME"] = "whisper-vet-voicemail-triage"

import opik
from openai import OpenAI
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai

TTS_MODEL = "tts-1"
TRANSCRIBE_MODEL = "whisper-1"
TRIAGE_MODEL = "gpt-4o-mini"

URGENCY_RANK = {"emergency": 0, "urgent": 1, "routine": 2}

TRIAGE_SYSTEM_PROMPT = """\
You are the triage desk at a small veterinary clinic. You read the transcript
of one voicemail and decide how fast the clinic must call the owner back.
Reply with JSON only, in exactly this shape:

{
  "caller": "the owner's name, as spoken",
  "pet": "the animal's name and species",
  "phone": "the callback number as spoken, digits only, or null",
  "urgency": "emergency | urgent | routine",
  "reason": "one sentence citing what the caller said"
}

Urgency levels:
- emergency: call back within minutes. Poisoning or toxin ingestion, trouble
  breathing, collapse, seizures, heavy bleeding, and rabbits or other small
  mammals that stop eating or passing droppings.
- urgent: call back today. Pain, limping, or a new symptom in an animal that
  is otherwise eating and alert.
- routine: no symptoms. Refills, bookings, general questions.

Judge by the symptoms, not by the caller's tone. Owners who say "this is
probably nothing" are often describing an emergency. Never give medical
advice and never state facts the caller did not say.
"""


@cache
def get_client() -> OpenAI:
    # track_openai wraps the client: every completion becomes an llm span with
    # token usage and cost, nested under the calling @track span. Built lazily
    # so importing this module needs no API key.
    return track_openai(OpenAI())


def load_voicemails() -> list[dict]:
    return json.loads((EXAMPLE_DIR / "data" / "voicemails.json").read_text())


def parse_triage(raw: str) -> dict:
    """Parse and validate the model's JSON; urgency must be a known level."""
    triage = json.loads(raw)
    triage["urgency"] = str(triage.get("urgency", "")).strip().lower()
    if triage["urgency"] not in URGENCY_RANK:
        raise ValueError(f"unknown urgency {triage['urgency']!r}")
    return triage


def build_callback_list(results: list[dict]) -> list[dict]:
    """Most urgent first; ties keep the order the voicemails arrived in."""
    return sorted(results, key=lambda r: URGENCY_RANK[r["urgency"]])


# A plain @track function is a general span: its arguments and return value
# appear as the span's input/output, and it nests under the active trace.
@opik.track(name="synthesize-voicemail")
def synthesize(voicemail: dict, audio_path: Path) -> dict:
    response = get_client().audio.speech.create(
        model=TTS_MODEL,
        voice=voicemail["voice"],
        input=voicemail["script"],
        response_format="mp3",
    )
    audio_path.write_bytes(response.content)
    return {"audio": audio_path.name, "voice": voicemail["voice"], "size_bytes": len(response.content)}


# Its output (the transcript) is what the pipeline *believes* was said; the
# attached MP3 is what was actually said. Compare them in the Opik UI.
@opik.track(name="transcribe")
def transcribe(audio_path: Path) -> str:
    with audio_path.open("rb") as audio_file:
        return get_client().audio.transcriptions.create(
            model=TRANSCRIBE_MODEL, file=audio_file, response_format="text"
        )


@opik.track(name="triage")
def triage(transcript: str) -> dict:
    response = get_client().chat.completions.create(
        model=TRIAGE_MODEL,
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return parse_triage(response.choices[0].message.content)


# The outermost @track call is the trace root: one voicemail, one trace.
@opik.track(name="triage-voicemail")
def triage_voicemail(voicemail: dict) -> dict:
    AUDIO_DIR.mkdir(exist_ok=True)
    audio_path = AUDIO_DIR / f"{voicemail['id']}.mp3"
    synthesize(voicemail, audio_path)
    transcript = transcribe(audio_path)
    result = triage(transcript)

    # Attachments are uploaded with the trace and rendered as a player in the
    # trace's Attachments tab; without this the audio is gone after the run.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(audio_path), content_type="audio/mpeg")]
    )
    return {"id": voicemail["id"], "transcript": transcript, **result}


def main() -> None:
    results = [triage_voicemail(vm) for vm in load_voicemails()]

    # evaluate.py replays these transcripts through the triage step.
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "transcripts.json").write_text(json.dumps(results, indent=2))

    print("\nCallback list (most urgent first)")
    for r in build_callback_list(results):
        print(f"  [{r['urgency']:<9}] {r['caller']} ({r['pet']}) {r['phone']} - {r['reason']}")

    # Traces are sent in a background thread; flush so they all arrive
    # before the process exits.
    opik.flush_tracker()
    print("\nDone. Open the whisper-vet-voicemail-triage project in Opik.")


if __name__ == "__main__":
    main()
