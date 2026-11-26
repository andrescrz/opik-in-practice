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
from parkguide.evaluation import mean_scores, run_experiment
from parkguide.graph import build_graph
from parkguide.retriever import KeywordRetriever

DEMO_QUESTIONS = [
    "How much does a backcountry permit cost and how far ahead can I book?",
    "Are dogs allowed on Ember Ridge?",
    "Can I bring my own firewood to Cinder Flat?",
    "Can I take my pooch on the hike up to the fire lookout?",
    "Is there a shuttle bus from the airport to the park?",
]


def make_app(retriever: KeywordRetriever, llm: ChatOpenAI, k: int):
    # track_langgraph attaches the tracer to the compiled graph: each invoke() becomes one
    # trace, with a span per node (retrieve, generate) and a nested llm span for the model call.
    # The graph structure is also sent so Opik can draw the node diagram.
    return track_langgraph(build_graph(retriever, llm, k=k), OpikTracer(project_name=PROJECT_NAME))


def main() -> None:
    retriever = KeywordRetriever(load_sections())
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    app = make_app(retriever, llm, k=4)
    for question in DEMO_QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")

    # Two experiments over the same dataset, differing only in how many sections are retrieved.
    for k in (4, 1):
        evaluation = run_experiment(make_app(retriever, llm, k=k), k, PROJECT_NAME)
        scores = ", ".join(f"{name}={value:.2f}" for name, value in mean_scores(evaluation).items())
        print(f"top-{k}-sections: {scores}")
        if evaluation.experiment_url:
            print(f"  {evaluation.experiment_url}")

    # Traces and experiment results are sent from background threads; flush so none are lost on exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
