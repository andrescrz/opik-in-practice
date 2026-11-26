import os

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

PROJECT_NAME = "langgraph-national-parks-rag"
# Routes every trace (including @opik.track spans) to this project instead of "Default Project".
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik
from langchain_openai import ChatOpenAI
from opik.integrations.langchain import OpikTracer, track_langgraph

from parkguide.corpus import load_sections
from parkguide.graph import build_graph
from parkguide.retriever import KeywordRetriever

DEMO_QUESTIONS = [
    "How much does a backcountry permit cost and how far ahead can I book?",
    "Are dogs allowed on Ember Ridge?",
    "Can I bring my own firewood to Cinder Flat?",
    "Is there a shuttle bus from the airport to the park?",
]


def main() -> None:
    retriever = KeywordRetriever(load_sections())
    graph = build_graph(retriever, ChatOpenAI(model="gpt-4o-mini", temperature=0))
    # track_langgraph attaches the tracer to the compiled graph: each invoke() becomes one
    # trace, with a span per node (retrieve, generate) and a nested llm span for the model call.
    # The graph structure is also sent so Opik can draw the node diagram.
    app = track_langgraph(graph, OpikTracer(project_name=PROJECT_NAME))
    for question in DEMO_QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")
    # Traces are sent from a background thread; flush so none are lost when the script exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
