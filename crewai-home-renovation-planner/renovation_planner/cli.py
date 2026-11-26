import argparse
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load the nearest .env (walking up from the working directory) before crewai reads keys.
load_dotenv(find_dotenv(usecwd=True))

from renovation_planner.crew import build_crew  # noqa: E402
from renovation_planner.inputs import load_brief, load_price_sheet  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan a kitchen and bath renovation with a three-agent crew.")
    parser.add_argument("--brief", type=Path, help="Path to a client brief (default: data/brief.md)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    brief = load_brief(args.brief) if args.brief else load_brief()
    result = build_crew().kickoff(inputs={"brief": brief, "price_sheet": load_price_sheet()})
    print("\n=== RENOVATION PLAN ===\n")
    print(result)


if __name__ == "__main__":
    main()
