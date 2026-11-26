import argparse

import dotenv

# Walks up from the working directory to the first .env (OPENAI_API_KEY).
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

from langchain_openai import ChatOpenAI

from .graph import build_graph

INCIDENT = (
    "Write the post-mortem for INC-2291: the Tidewater checkout outage on "
    "12 March, when customers could not complete payments for 84 minutes."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft a blameless post-mortem.")
    parser.add_argument("incident", nargs="?", default=INCIDENT)
    args = parser.parse_args()

    app = build_graph(ChatOpenAI(model="gpt-4o-mini", temperature=0))
    result = app.invoke({"incident": args.incident})

    print("Questions the planner raised:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\nThe investigator produced {len(result['findings'])} findings. Post-mortem:\n")
    print(result["postmortem"])
