import os
import pathlib

import dotenv

PROJECT_NAME = "dspy-board-game-rules-qa"
MODEL = "openai/gpt-4o-mini"
COMPILED_PATH = pathlib.Path(__file__).parents[1] / "compiled" / "program.json"


def load_env() -> None:
    # Walk up from this folder to the first .env so the example works both
    # standalone and inside a larger repo.
    dotenv.load_dotenv(dotenv.find_dotenv(usecwd=False) or None)
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)
