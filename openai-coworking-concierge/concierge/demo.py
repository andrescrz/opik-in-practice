"""Scripted guests, so the demo runs with no typing."""

from dataclasses import dataclass


@dataclass
class Scenario:
    session_id: str
    turns: list[str]
    rating: float
    rating_reason: str


SCENARIOS = [
    Scenario(
        "day-pass-hot-desk",
        [
            "Hi! I'm visiting Lisbon for a week and need a desk. What are my options?",
            "Hot desk sounds right. Can I just turn up on Tuesday, and what time do you open for day-pass people?",
            "Perfect. And can I take a video call from my desk?",
        ],
        1.0,
        "Guest got hours, price and the call-booth rule, and booked.",
    ),
    Scenario(
        "board-meeting-room",
        [
            "We need a room for 10 people next Thursday afternoon, 2 hours. What do you have?",
            "What does that cost, and what's in the room?",
            "Something came up, and we might cancel the evening before. Do we lose the money?",
        ],
        1.0,
        "Guest got the right room, price and the 24-hour cancellation rule.",
    ),
    Scenario(
        "guest-with-dog",
        [
            "Can I bring my dog to work on Mondays?",
            "OK. Is there somewhere nearby to park a van overnight, then?",
        ],
        0.0,
        "Neither dogs nor parking are covered; guest left without an answer.",
    ),
]
