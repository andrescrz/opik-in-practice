from functools import partial

from langgraph.graph import END, START, StateGraph

from .corpus import load_corpus
from .nodes import investigator, planner, route_investigation, writer
from .state import PostmortemState


def build_graph(llm):
    """planner -> investigator (loops once per question) -> writer."""
    corpus = load_corpus()
    graph = StateGraph(PostmortemState)
    graph.add_node("planner", partial(planner, llm=llm))
    graph.add_node("investigator", partial(investigator, llm=llm, corpus=corpus))
    graph.add_node("writer", partial(writer, llm=llm))
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "investigator")
    graph.add_conditional_edges(
        "investigator",
        route_investigation,
        {"investigator": "investigator", "writer": "writer"},
    )
    graph.add_edge("writer", END)
    return graph.compile()
