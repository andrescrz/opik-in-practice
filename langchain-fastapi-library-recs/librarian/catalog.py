"""Offline catalog of the (fictional) Alder Creek Branch Library, with keyword search."""

import json
import re
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.json"

STOPWORDS = {
    "a", "an", "and", "the", "i", "me", "my", "to", "of", "for", "in", "on", "with", "that",
    "is", "it", "something", "any", "some", "want", "like", "something", "book", "books",
    "read", "reading", "recommend", "recommendation", "please", "you", "have", "do", "are",
    "was", "be", "about", "more", "less", "than", "but", "not", "too", "kind", "looking",
}


def load_catalog(path: Path = CATALOG_PATH) -> list[dict]:
    return json.loads(path.read_text())


def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def score(book: dict, query_tokens: set[str]) -> float:
    # Tags and genre are the curated vocabulary, so they count double against free-text summary words.
    curated = tokens(" ".join(book["tags"]) + " " + book["genre"])
    prose = tokens(book["title"] + " " + book["summary"])
    return 2.0 * len(query_tokens & curated) + 1.0 * len(query_tokens & prose)


def search_catalog(query: str, k: int = 4, catalog: list[dict] | None = None) -> list[dict]:
    catalog = catalog if catalog is not None else load_catalog()
    query_tokens = tokens(query)
    ranked = sorted(
        ((score(b, query_tokens), b) for b in catalog),
        key=lambda pair: (-pair[0], pair[1]["title"]),
    )
    return [b for s, b in ranked[:k] if s > 0]


def format_books(books: list[dict]) -> str:
    if not books:
        return "(no catalog matches)"
    lines = []
    for b in books:
        stock = f"{b['copies_available']} copies on shelf" if b["copies_available"] else "all copies out; holds open"
        lines.append(
            f"- {b['title']} by {b['author']} ({b['genre']}, {b['pages']} pages, {b['year']}): "
            f"{b['summary']} Tags: {', '.join(b['tags'])}. [{stock}]"
        )
    return "\n".join(lines)
