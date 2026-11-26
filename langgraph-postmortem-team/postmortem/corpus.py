"""The offline incident corpus: every blank-line-separated block in data/ is one searchable chunk."""

import math
import pathlib
import re

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# Question filler that would otherwise look rare in a small corpus and skew ranking.
STOPWORDS = frozenset(
    "the a an and or of to in for is are was were be been being what how why "
    "when which who whom should would could can may might must with on by as "
    "at it its if into from that this these those do does did not no so such "
    "any some during after before there their".split()
)


def load_corpus(data_dir: pathlib.Path = DATA_DIR) -> list[dict]:
    chunks = []
    for path in sorted(data_dir.glob("*")):
        if path.suffix not in {".md", ".txt"}:
            continue
        title, *blocks = [b.strip() for b in path.read_text().split("\n\n") if b.strip()]
        for block in blocks:
            chunks.append({"source": path.name, "text": f"{title.lstrip('# ')}\n{block}"})
    return chunks


def rarity(term: str, corpus: list[dict]) -> float:
    """Weight a term by how few chunks contain it (a tiny IDF)."""
    containing = sum(1 for c in corpus if term in c["text"].lower())
    return math.log(len(corpus) / containing) if containing else 0.0


def search(query: str, corpus: list[dict], k: int = 3) -> list[dict]:
    terms = set(re.findall(r"[a-z0-9]+", query.lower())) - STOPWORDS

    def score(chunk: dict) -> float:
        text = chunk["text"].lower()
        return sum(rarity(t, corpus) for t in terms if t in text)

    return sorted(corpus, key=score, reverse=True)[:k]
