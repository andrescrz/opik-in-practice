"""The illustration brief, in two versions.

v1 is what every team writes first. v2 adds the rules an art director would
ask for after seeing v1's pictures: a fixed look for the hero, a palette,
no lettering, and a landscape-friendly composition.
"""
import json
import re
from pathlib import Path

BRIEF_NAME = "storybook-illustration-brief"

BRIEF_V1 = """Children's book illustration for page {{page}} of "The Lantern Hedgehog".
Setting: {{setting}}.
Action: {{action}}.
Mood: {{mood}}."""

BRIEF_V2 = """Children's book illustration for page {{page}} of "The Lantern Hedgehog".
Setting: {{setting}}.
Action: {{action}}.
Mood: {{mood}}.

Style rules:
- Soft watercolor with visible paper grain, warm amber light, muted teal shadows.
- Pip is a small round hedgehog with a cream face and a red knitted scarf, the same in every picture.
- No text, letters, captions or speech bubbles anywhere in the image.
- Keep the lower third calm and uncluttered so the story text can sit on top of it."""

V2_CHANGE = "Add art-direction rules: watercolor palette, fixed look for Pip, no lettering, calm lower third"

SCENES_FILE = Path(__file__).resolve().parent.parent / "data" / "scenes.json"


def load_scenes(path: Path = SCENES_FILE) -> list[dict]:
    return json.loads(path.read_text())


def render(template: str, **values: object) -> str:
    """Fill {{name}} placeholders; fail loudly on a missing variable."""

    def fill(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"brief needs a value for {key!r}")
        return str(values[key])

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", fill, template)
