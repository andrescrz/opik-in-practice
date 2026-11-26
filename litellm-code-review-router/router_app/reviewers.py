"""Prompt building and loading of the fictional patches."""

import json
from pathlib import Path

PATCHES_FILE = Path(__file__).resolve().parent.parent / "data" / "patches.json"

SYSTEM = (
    "You are a senior engineer reviewing a small patch. Reply with a one-sentence "
    "summary of the change, then a 'Risk:' line (low, medium or high) with a short reason."
)


def load_patches(path: Path = PATCHES_FILE) -> list[dict]:
    return json.loads(path.read_text())


def build_messages(patch: dict) -> list[dict]:
    user = f"Patch: {patch['title']}\n\n```diff\n{patch['diff']}\n```"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
