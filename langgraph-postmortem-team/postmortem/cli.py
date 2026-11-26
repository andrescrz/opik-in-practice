import argparse
import os

import dotenv

PROJECT_NAME = "langgraph-postmortem-team"
# Every trace from this process lands in this Opik project (set before opik is imported).
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

# Walks up from the working directory to the first .env (OPENAI_API_KEY and, for a
# non-default Opik server, OPIK_URL_OVERRIDE / OPIK_API_KEY). Must run before any Opik client exists.
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

import opik
from langchain_openai import ChatOpenAI
from opik.integrations.langchain import OpikTracer, track_langgraph

from .graph import build_graph

INCIDENT = (
    "Write the post-mortem for INC-2291: the Tidewater checkout outage on "
    "12 March, when customers could not complete payments for 84 minutes."
)


def traced(app):
    # xray=True expands subgraphs so the agent-graph tab in Opik draws planner ->
    # investigator (with its self-loop) -> writer next to the span tree.
    tracer = OpikTracer(graph=app.get_graph(xray=True), project_name=PROJECT_NAME)
    # track_langgraph injects the tracer into the graph's default config: each invoke()
    # becomes ONE trace, each node pass a span, and each ChatOpenAI call an llm span
    # (tokens + cost) nested under the node that made it.
    return track_langgraph(app, tracer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft a blameless post-mortem.")
    parser.add_argument("incident", nargs="?", default=INCIDENT)
    args = parser.parse_args()

    app = traced(build_graph(ChatOpenAI(model="gpt-4o-mini", temperature=0)))
    result = app.invoke({"incident": args.incident})

    print("Questions the planner raised:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\nThe investigator produced {len(result['findings'])} findings. Post-mortem:\n")
    print(result["postmortem"])

    # Traces are sent from a background thread; without a flush a short-lived
    # CLI can exit before the last spans are delivered.
    opik.flush_tracker()
