"""The classifier under test: one chat call that labels a review by intent."""

import os

import dotenv

PROJECT_NAME = "optimizer-app-review-classifier"

# Walks up from this folder to the first .env (the repo root in a monorepo).
# Must run before the first Opik client exists so OPIK_URL_OVERRIDE etc. apply.
dotenv.load_dotenv(dotenv.find_dotenv())
# Opik reads the default project from this variable; without it traces go to "Default Project".
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import opik
from openai import OpenAI
from opik.integrations.openai import track_openai

MODEL = "gpt-4o-mini"

# A typical first draft: it names the intents but gives no definitions for the
# edge cases and never says to answer with the label alone.
# A typical first draft: the intents are loose prose and nothing fixes the
# label vocabulary, so answers like "Bug" or "Billing issue" miss the exact label.
BASELINE_SYSTEM = """\
You read app-store reviews for Pebblepad, a budgeting app. Give each review a
short label for what the reviewer wants: something like a bug, a feature idea,
praise, a billing issue, or a usability question."""

# track_openai wraps the client: every completion becomes an llm span in the
# project, with token usage and cost.
client = track_openai(OpenAI(), project_name=PROJECT_NAME)


def normalize(answer: str) -> str:
    """Lowercase, trim quotes/punctuation, and unify separators so 'Bug Report.' == 'bug_report'."""
    cleaned = answer.strip().lower().strip(".!\"'` *")
    return cleaned.replace(" ", "_").replace("-", "_")


def intent_match(expected: str, answer: str) -> float:
    return 1.0 if normalize(answer) == expected else 0.0


# @track makes each classification one trace; the wrapped client's llm span nests
# under it as a child, so a trace shows review in, label out, and the model call.
@opik.track(name="classify_review", project_name=PROJECT_NAME)
def classify(review: str, system: str = BASELINE_SYSTEM) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": review},
        ],
    )
    return response.choices[0].message.content or ""
