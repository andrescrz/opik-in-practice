"""Guest ratings, logged to Opik after the conversations are over."""

import opik

SCORE_NAME = "guest-satisfaction"


def build_scores(ratings) -> list[dict]:
    """ratings: (trace_id, value, reason) tuples -> Opik feedback-score payloads."""
    return [
        {"id": trace_id, "name": SCORE_NAME, "value": value, "reason": reason}
        for trace_id, value, reason in ratings
    ]


def log_guest_ratings(ratings, client=None) -> None:
    # The traces are sent asynchronously, so flush first: feedback can only be
    # attached to a trace that already exists server-side.
    opik.flush_tracker()
    client = client or opik.Opik()
    # Adds a guest-satisfaction column to the project's trace table, scored on
    # the last turn of each conversation.
    client.log_traces_feedback_scores(build_scores(ratings))
