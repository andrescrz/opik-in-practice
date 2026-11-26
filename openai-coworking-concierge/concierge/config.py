"""Environment loading and client construction."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

MODEL = "gpt-4o-mini"
PROJECT = "openai-coworking-concierge"


def load_env() -> None:
    """Load the nearest .env above the working directory, if there is one."""
    load_dotenv(find_dotenv(usecwd=True))
    # Must be set before the first Opik client exists; it decides which Opik
    # project every trace in this app lands in.
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT)


def make_client():
    from openai import OpenAI
    from opik.integrations.openai import track_openai

    # track_openai wraps the client: every completion becomes an llm span with
    # model, messages, token usage and a cost estimate.
    return track_openai(OpenAI())


DATA_FILE = Path(__file__).parent / "data" / "space.json"
