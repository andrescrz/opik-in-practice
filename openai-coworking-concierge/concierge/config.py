"""Environment loading and client construction."""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv

MODEL = "gpt-4o-mini"


def load_env() -> None:
    """Load the nearest .env above the working directory, if there is one."""
    load_dotenv(find_dotenv(usecwd=True))


def make_client():
    from openai import OpenAI

    return OpenAI()


DATA_FILE = Path(__file__).parent / "data" / "space.json"
