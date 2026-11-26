"""Illustrate two storybook pages with each of two brief versions (4 images)."""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env before anything creates an Opik client, so OPIK_URL_OVERRIDE and
# OPIK_WORKSPACE point the SDK at your Opik server.
load_dotenv(find_dotenv(usecwd=False))
PROJECT = "openai-py-storybook-illustrations"
# Every trace from this process lands in this Opik project.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT)

import opik  # noqa: E402

from storybook.briefs import load_scenes  # noqa: E402
from storybook.illustrate import illustrate, make_client  # noqa: E402
from storybook.library import brief_diff, ensure_brief_versions  # noqa: E402

OUTPUT = Path(__file__).parent / "output"


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    opik_client = opik.Opik(project_name=PROJECT)
    v1, v2 = ensure_brief_versions(opik_client, PROJECT)
    print(f"Prompt library: {v1.name} has v1 ({v1.commit}) and v2 ({v2.commit})\n")
    print(brief_diff(v1, v2), "\n")

    client = make_client()
    for brief in (v1, v2):
        for scene in load_scenes():
            path = illustrate(client, brief, scene, OUTPUT)
            print(f"{brief.version} {scene['id']} -> {path} ({path.stat().st_size // 1024} KiB)")

    # Traces and attachments upload in the background; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
