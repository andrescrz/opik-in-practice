"""Roll the latest kickoff trace up into tokens and dollars per agent.

Opik records usage and cost on the llm spans only; the agent spans above them
carry none. This script walks each llm span up to its agent span and sums.
"""

import argparse
from collections import defaultdict

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import opik  # noqa: E402

from renovation_planner.crew import PROJECT_NAME  # noqa: E402


def cost_by_agent(spans) -> dict[str, dict[str, float]]:
    """Sum llm-span tokens and cost under the agent span that owns them.

    The agent span is the direct child of a "Task: ..." span.
    """
    by_id = {s.id: s for s in spans}
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    for span in spans:
        if span.type != "llm":
            continue
        node = span
        while node is not None:
            parent = by_id.get(node.parent_span_id)
            if parent is not None and parent.name.startswith("Task: "):
                totals[node.name]["tokens"] += (span.usage or {}).get("total_tokens", 0)
                totals[node.name]["cost"] += span.total_estimated_cost or 0.0
                break
            node = parent
    return dict(totals)


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="Per-agent tokens and cost for the latest kickoff trace.").parse_args(argv)
    client = opik.Opik(project_name=PROJECT_NAME)
    # Reading back needs the trace to have been flushed by the run that produced it.
    trace = client.search_traces(project_name=PROJECT_NAME, max_results=1)[0]
    spans = client.search_spans(project_name=PROJECT_NAME, trace_id=trace.id, max_results=500)
    totals = cost_by_agent(spans)
    print(f"trace {trace.id}  total ${trace.total_estimated_cost:.5f}")
    for agent, t in sorted(totals.items(), key=lambda kv: -kv[1]["cost"]):
        print(f"  {agent:<22} {int(t['tokens']):>6} tokens  ${t['cost']:.5f}")


if __name__ == "__main__":
    main()
