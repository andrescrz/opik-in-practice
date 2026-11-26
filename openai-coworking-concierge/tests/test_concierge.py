from types import SimpleNamespace

from concierge.feedback import build_scores, log_guest_ratings
from concierge.knowledge import load_space, render_facts
from concierge.prompts import build_system_prompt
from concierge.session import Session


class StubClient:
    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, model, messages):
        self.calls.append(list(messages))
        message = SimpleNamespace(content=f"reply {len(self.calls)}")
        usage = SimpleNamespace(total_tokens=42)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def test_facts_cover_desks_rooms_and_rules():
    facts = render_facts(load_space())
    assert "Press Room (8 seats, EUR 28 per hour)" in facts
    assert "hot desk: EUR 18 per day" in facts
    assert "Bicycles live in the yard rack" in facts


def test_system_prompt_names_the_space_and_tells_it_not_to_guess():
    prompt = build_system_prompt(load_space())
    assert prompt.startswith("You are the front-desk concierge at Larkspur Yard")
    assert "Never guess" in prompt


def test_session_keeps_history_across_turns():
    client = StubClient()
    session = Session(client, "system", "guest-1")
    session.ask("first")
    session.ask("second")
    assert [m["role"] for m in client.calls[1]] == ["system", "user", "assistant", "user"]
    assert session.last_usage.total_tokens == 42


def test_traced_ask_works_with_tracking_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    session = Session(StubClient(), "system", "guest-1")
    assert session.ask("hello") == "reply 1"


def test_build_scores_shape():
    scores = build_scores([("t1", 1.0, "happy"), ("t2", 0.0, "no answer")])
    assert scores[1] == {
        "id": "t2",
        "name": "guest-satisfaction",
        "value": 0.0,
        "reason": "no answer",
    }


def test_log_guest_ratings_sends_scores_to_client():
    sent = []
    client = SimpleNamespace(log_traces_feedback_scores=sent.append)
    log_guest_ratings([("t1", 1.0, "happy")], client=client)
    assert sent[0][0]["id"] == "t1"
