"""The classifier under test: one chat call that labels a review by intent."""

import dotenv
from openai import OpenAI

# Walks up from this folder to the first .env (the repo root in a monorepo).
dotenv.load_dotenv(dotenv.find_dotenv())

MODEL = "gpt-4o-mini"

# A typical first draft: the intents are described in prose and nothing says
# what shape the answer should take.
BASELINE_SYSTEM = """\
You read app-store reviews for Pebblepad, a budgeting app. Work out what the
reviewer is mainly after: reporting a bug, asking for a new feature, praising
the app, complaining about billing, or confused about how to use something.
Say which one it is."""

client = OpenAI()


def normalize(answer: str) -> str:
    """Lowercase, trim quotes/punctuation, and unify separators so 'Bug Report.' == 'bug_report'."""
    cleaned = answer.strip().lower().strip(".!\"'` *")
    return cleaned.replace(" ", "_").replace("-", "_")


def intent_match(expected: str, answer: str) -> float:
    return 1.0 if normalize(answer) == expected else 0.0


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
