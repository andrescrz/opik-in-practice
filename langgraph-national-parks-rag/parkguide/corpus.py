import pathlib
from dataclasses import dataclass

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class Section:
    source: str
    heading: str
    text: str

    def render(self) -> str:
        return f"[{self.source}] {self.heading}\n{self.text}"


def split_markdown(source: str, markdown: str) -> list[Section]:
    """One section per '##' heading, so a retrieved chunk covers one topic."""
    sections = []
    for block in markdown.split("\n## ")[1:]:
        heading, _, body = block.partition("\n")
        sections.append(Section(source, heading.strip(), " ".join(body.split())))
    return sections


def load_sections(data_dir: pathlib.Path = DATA_DIR) -> list[Section]:
    sections = []
    for path in sorted(data_dir.glob("*.md")):
        sections.extend(split_markdown(path.stem, path.read_text()))
    return sections
