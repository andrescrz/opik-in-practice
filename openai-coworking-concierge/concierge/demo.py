"""Scripted guests, so the demo runs with no typing."""

from dataclasses import dataclass


@dataclass
class Scenario:
    session_id: str
    turns: list[str]


SCENARIOS = [
    Scenario(
        "day-pass-hot-desk",
        [
            "Hi! I'm visiting Lisbon for a week and need a desk. What are my options?",
            "Hot desk sounds right. Can I just turn up on Tuesday, and what time do you open for day-pass people?",
            "Perfect. And can I take a video call from my desk?",
        ],
    ),
    Scenario(
        "board-meeting-room",
        [
            "We need a room for 10 people next Thursday afternoon, 2 hours. What do you have?",
            "What does that cost, and what's in the room?",
            "Something came up, and we might cancel the evening before. Do we lose the money?",
        ],
    ),
    Scenario(
        "guest-with-dog",
        [
            "Can I bring my dog to work on Mondays?",
            "OK. Is there somewhere nearby to park a van overnight, then?",
        ],
    ),
]
