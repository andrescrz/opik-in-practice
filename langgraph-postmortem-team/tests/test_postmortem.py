from types import SimpleNamespace

from postmortem.cli import traced
from postmortem.corpus import load_corpus, search
from postmortem.graph import build_graph
from postmortem.nodes import InvestigationPlan, route_investigation


class StubLLM:
    """Stands in for ChatOpenAI: a fixed plan, then canned text for every other call."""

    def __init__(self, questions):
        self.questions = questions

    def with_structured_output(self, _schema):
        return SimpleNamespace(invoke=lambda _m: InvestigationPlan(questions=self.questions))

    def invoke(self, messages):
        return SimpleNamespace(content=f"answer to: {messages[-1][1][:40]}")


def test_corpus_chunks_every_artifact():
    corpus = load_corpus()
    assert {c["source"] for c in corpus} == {
        "alerts.md", "chat-excerpts.md", "gateway-logs.txt",
        "runbooks-and-reviews.md", "timeline.md",
    }


def test_search_finds_the_muted_alert():
    hits = search("which alert was muted by the maintenance window", load_corpus())
    assert hits[0]["source"] == "alerts.md"
    assert "maintenance-window" in hits[0]["text"]


def test_route_loops_until_all_questions_answered():
    state = {"questions": ["a", "b"], "findings": [{}]}
    assert route_investigation(state) == "investigator"
    state["findings"].append({})
    assert route_investigation(state) == "writer"


def test_graph_runs_one_investigator_pass_per_question():
    app = build_graph(StubLLM(["q1?", "q2?", "q3?"]))
    result = app.invoke({"incident": "INC-2291"})
    assert [f["question"] for f in result["findings"]] == ["q1?", "q2?", "q3?"]
    assert result["postmortem"].startswith("answer to:")


def test_traced_graph_still_runs_with_tracking_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    app = traced(build_graph(StubLLM(["only question?"])))
    assert len(app.invoke({"incident": "INC-2291"})["findings"]) == 1
