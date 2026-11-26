import pathlib
import re

RULEBOOK_PATH = pathlib.Path(__file__).parents[1] / "data" / "rulebook.md"
HEADING = re.compile(r"^## §(\d+\.\d+) .+$", re.MULTILINE)


def load_rulebook() -> str:
    return RULEBOOK_PATH.read_text(encoding="utf-8")


def section_ids(rulebook: str) -> list[str]:
    return HEADING.findall(rulebook)
