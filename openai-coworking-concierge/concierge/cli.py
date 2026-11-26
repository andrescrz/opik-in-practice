"""Command line entry point: `concierge` (scripted demo) or `concierge --chat`."""

import argparse
import uuid

from concierge.config import load_env, make_client
from concierge.demo import SCENARIOS
from concierge.knowledge import load_space
from concierge.prompts import build_system_prompt
from concierge.session import Session


def run_demo(client, system_prompt: str) -> None:
    for scenario in SCENARIOS:
        print(f"\n=== {scenario.session_id} ===")
        session = Session(client, system_prompt, scenario.session_id)
        for turn in scenario.turns:
            print(f"\nGuest: {turn}")
            print(f"Concierge: {session.ask(turn)}")
            print(f"  [{session.last_usage.total_tokens} tokens]")


def run_chat(client, system_prompt: str) -> None:
    session = Session(client, system_prompt, f"chat-{uuid.uuid4().hex[:8]}")
    print(f"Larkspur Yard front desk (session {session.session_id}). Ctrl+C to leave.")
    while True:
        message = input("\nYou: ").strip()
        if message:
            print(f"Concierge: {session.ask(message)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Larkspur Yard concierge")
    parser.add_argument("--chat", action="store_true", help="talk to it yourself")
    args = parser.parse_args()

    load_env()
    system_prompt = build_system_prompt(load_space())
    client = make_client()
    try:
        (run_chat if args.chat else run_demo)(client, system_prompt)
    except KeyboardInterrupt:
        print("\nGoodbye!")
