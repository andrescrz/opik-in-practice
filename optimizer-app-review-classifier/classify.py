"""The classifier under test: one chat call that labels a review by intent."""

import functools
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

# A typical first draft: it names the five intents but also asks for a reason,
# so answers come back as "bug_report - the app crashes" and fail exact match.
BASELINE_SYSTEM = """\
You read app-store reviews for Pebblepad, a budgeting app. Tag each review with
its intent: bug_report, feature_request, praise, billing_complaint or
usability_confusion. Then add a short note on why you chose it."""

@functools.cache
def get_client():
    # track_openai wraps the client: every completion becomes an llm span in the
    # project, with token usage and cost. Built lazily so importing needs no key.
    return track_openai(OpenAI(), project_name=PROJECT_NAME)


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
    response = get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": review},
        ],
    )
    return response.choices[0].message.content or ""
