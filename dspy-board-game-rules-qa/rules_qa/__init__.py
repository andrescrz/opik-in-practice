"""Lanternfall rules QA: a DSPy program that compiles its own few-shot prompt."""

from .config import load_env

# Load .env before any submodule imports opik: the SDK reads its URL,
# workspace and project from the environment when the client is created.
load_env()
