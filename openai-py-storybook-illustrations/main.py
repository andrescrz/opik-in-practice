"""Illustrate two storybook pages with each of two brief versions (4 images)."""
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=False))

from storybook.briefs import BRIEF_V1, BRIEF_V2, load_scenes, render  # noqa: E402
from storybook.illustrate import generate_png, make_client  # noqa: E402

OUTPUT = Path(__file__).parent / "output"


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    client = make_client()
    for version, template in (("v1", BRIEF_V1), ("v2", BRIEF_V2)):
        for scene in load_scenes():
            prompt = render(template, **scene)
            png, _ = generate_png(client, prompt)
            path = OUTPUT / f"{version}-{scene['id']}.png"
            path.write_bytes(png)
            print(f"{version} {scene['id']} -> {path} ({len(png) // 1024} KiB)")


if __name__ == "__main__":
    main()
