"""Insurance claims intake: a triage agent hands off to auto, home and travel-medical specialists."""

import json
import os
import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from agents import Agent, Runner, function_tool

import insurer

MODEL = "gpt-4o-mini"


@function_tool
def lookup_claim(claim_id: str) -> str:
    """Look up the status, amount and adjuster notes of an existing claim by its id."""
    return json.dumps(insurer.lookup_claim(claim_id))


@function_tool
def check_coverage(policy_id: str, peril: str) -> str:
    """Check whether a policy covers a peril (e.g. collision, flood, emergency_care) and return the deductible."""
    return json.dumps(insurer.check_coverage(policy_id, peril))


@function_tool
def open_claim(policy_id: str, description: str, estimated_amount_usd: float) -> str:
    """Open a new claim on an active policy and return the claim id."""
    return json.dumps(insurer.open_claim(policy_id, description, estimated_amount_usd))


SPECIALIST_RULES = (
    "Always call check_coverage before telling the customer whether they are covered. "
    "Only call open_claim after the customer explicitly asks you to file. "
    "If coverage is denied, say why and do not open a claim. Keep replies under four sentences."
)

auto_agent = Agent(
    name="Auto Claims Agent",
    handoff_description="Car accidents, theft, glass damage and rental reimbursement.",
    instructions="You handle auto insurance claims. " + SPECIALIST_RULES,
    model=MODEL,
    tools=[check_coverage, open_claim, lookup_claim],
)

home_agent = Agent(
    name="Home Claims Agent",
    handoff_description="Fire, water, wind and theft damage to a house or its contents.",
    instructions="You handle homeowner claims. " + SPECIALIST_RULES,
    model=MODEL,
    tools=[check_coverage, open_claim, lookup_claim],
)

travel_agent = Agent(
    name="Travel Medical Agent",
    handoff_description="Medical emergencies, evacuation and trip interruption while travelling.",
    instructions="You handle travel-medical claims. " + SPECIALIST_RULES,
    model=MODEL,
    tools=[check_coverage, open_claim, lookup_claim],
)

triage_agent = Agent(
    name="Claims Triage Agent",
    instructions=(
        "You are the first point of contact at Larkspur Mutual. Decide which line the "
        "request belongs to (auto, home or travel medical) and hand off to that specialist "
        "immediately. Do not answer coverage questions yourself."
    ),
    model=MODEL,
    handoffs=[auto_agent, home_agent, travel_agent],
)

CONVERSATIONS = {
    "fender-bender": [
        "Hi, I'm Marta Okafor, policy AU-4471. I rear-ended another car this morning. Am I covered for collision?",
        "Yes, please file it. The body shop estimates $2,300.",
    ],
    "basement-flood": [
        "Policy HM-2290. Heavy rain flooded my basement overnight and ruined the carpet. Can I claim?",
        "Okay. Then what is the status of my kitchen pipe claim CL-7003?",
    ],
    "er-abroad": [
        "I'm Owen Fairweather, policy TM-5513. I was taken to an emergency room in Porto with appendicitis. Is that covered, and what do I pay?",
    ],
}


def run_demo() -> None:
    for name, turns in CONVERSATIONS.items():
        conversation_id = f"{name}-{uuid.uuid4().hex[:8]}"
        print(f"\n=== {name} ({conversation_id}) ===")
        history = []
        for message in turns:
            print(f"\nCustomer: {message}")
            history.append({"role": "user", "content": message})
            result = Runner.run_sync(triage_agent, history)
            print(f"{result.last_agent.name}: {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    run_demo()
