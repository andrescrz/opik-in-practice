"""The space's facts, loaded from data/space.json and rendered as prompt text."""

import json

from concierge.config import DATA_FILE


def load_space(path=DATA_FILE) -> dict:
    return json.loads(path.read_text())


def render_facts(space: dict) -> str:
    desks = "\n".join(
        f"- {d['type']}: {d['price']}. {d['notes']}" for d in space["desks"]
    )
    rooms = "\n".join(
        f"- {r['name']} ({r['seats']} seats, {r['price']}): {r['kit']}"
        for r in space["rooms"]
    )
    booking = "\n".join(f"- {line}" for line in space["booking"])
    rules = "\n".join(f"- {line}" for line in space["rules"])
    return (
        f"Hours: {space['hours']}\n\n"
        f"Desks:\n{desks}\n\nMeeting rooms:\n{rooms}\n\n"
        f"Booking and cancellation:\n{booking}\n\nHouse rules:\n{rules}"
    )
