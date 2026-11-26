from llama_index.core import VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine

from . import config

GUIDANCE = (
    "You answer students' questions about course syllabi. Use only the retrieved excerpts, "
    "name the course you are answering about, and quote figures exactly (percentages, "
    "hours, times, course codes). If the excerpts do not cover the question, say so."
)


def make_engine(index: VectorStoreIndex) -> BaseQueryEngine:
    return index.as_query_engine(similarity_top_k=config.TOP_K)


def ask(engine: BaseQueryEngine, question: str) -> dict:
    response = engine.query(f"{GUIDANCE}\n\nQuestion: {question}")
    return {
        "answer": str(response),
        "sources": [
            {"file": n.metadata.get("file_name"), "text": n.text} for n in response.source_nodes
        ],
    }
