from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .retriever import KeywordRetriever

SYSTEM_PROMPT = (
    "You are the visitor-information assistant for Larkspur Hollow National Park. "
    "Answer using only the guide excerpts below. If they do not cover the question, "
    "say you don't know and suggest asking at the Visitor Centre. Be concise.\n\n"
)


class State(TypedDict):
    question: str
    context: list[str]
    answer: str


def build_graph(retriever: KeywordRetriever, llm: Any, k: int = 4):
    def retrieve(state: State) -> dict:
        sections = retriever.search(state["question"], k=k)
        return {"context": [s.render() for s in sections]}

    def generate(state: State) -> dict:
        context = "\n\n---\n\n".join(state["context"]) or "(no excerpts found)"
        reply = llm.invoke([("system", SYSTEM_PROMPT + context), ("user", state["question"])])
        return {"answer": reply.content}

    graph = StateGraph(State)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
