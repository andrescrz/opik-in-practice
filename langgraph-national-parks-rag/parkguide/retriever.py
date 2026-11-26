import math
import re
from collections import Counter

from .corpus import Section

STOPWORDS = {
    "a", "an", "and", "are", "at", "be", "can", "do", "does", "for", "from", "how",
    "i", "if", "in", "is", "it", "my", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "with", "you", "there", "any",
}


def tokenize(text: str) -> list[str]:
    """Lowercase words with a crude plural strip; no embeddings, no network."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in STOPWORDS]


class KeywordRetriever:
    """BM25 over the guide's sections. Keyword-only, so it misses paraphrases."""

    def __init__(self, sections: list[Section], k1: float = 1.5, b: float = 0.75):
        self.sections = sections
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(f"{s.heading} {s.heading} {s.text}")) for s in sections]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / len(self.lengths)
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query_terms: list[str], index: int) -> float:
        doc, length = self.docs[index], self.lengths[index]
        total = 0.0
        for term in query_terms:
            tf = doc.get(term, 0)
            if tf:
                norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                total += self.idf[term] * tf * (self.k1 + 1) / norm
        return total

    def search(self, question: str, k: int = 4) -> list[Section]:
        terms = tokenize(question)
        ranked = sorted(range(len(self.sections)), key=lambda i: self.score(terms, i), reverse=True)
        return [self.sections[i] for i in ranked[:k] if self.score(terms, i) > 0]
