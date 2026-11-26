from types import SimpleNamespace

from renovation_planner.agents import MODEL, build_agents
from renovation_planner.cli import parse_args
from renovation_planner.costs import cost_by_agent
from renovation_planner.crew import build_crew
from renovation_planner.inputs import load_brief, load_price_sheet
from renovation_planner.tasks import build_tasks


def test_price_sheet_is_rendered_as_readable_lines():
    sheet = load_price_sheet()
    assert sheet.splitlines()[0].startswith("item | unit")
    assert "Quartz countertop | sq ft | 85" in sheet


def test_brief_states_the_budget_ceiling():
    assert "38,000" in load_brief()


def test_tasks_chain_context_in_order():
    tasks = build_tasks(build_agents())
    assert [t.name for t in tasks] == ["Define the scope", "Estimate the budget", "Plan the schedule"]
    assert tasks[1].context == [tasks[0]]
    assert tasks[2].context == [tasks[0], tasks[1]]


def test_every_agent_uses_the_cheap_model():
    assert all(a.llm.model == MODEL for a in build_agents().values())


def test_cli_brief_override():
    assert str(parse_args(["--brief", "x.md"]).brief) == "x.md"


def test_build_crew_with_tracking_disabled(monkeypatch):
    # track_crewai is a no-op when tracking is disabled, so a traced crew builds like a plain one.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    crew = build_crew()
    assert len(crew.agents) == 3 and len(crew.tasks) == 3


def _span(id, name, type, parent=None, tokens=0, cost=None):
    return SimpleNamespace(
        id=id, name=name, type=type, parent_span_id=parent,
        usage={"total_tokens": tokens} if tokens else None, total_estimated_cost=cost,
    )


def test_cost_by_agent_rolls_llm_spans_up_to_agent():
    spans = [
        _span("k", "kickoff", "general"),
        _span("t1", "Task: Define the scope", "general", "k"),
        _span("a1", "Scope Planner", "general", "t1"),
        _span("f1", "Flow.kickoff_async", "general", "a1"),
        _span("l1", "chat_completion_create", "llm", "f1", 100, 0.001),
        _span("l2", "chat_completion_create", "llm", "f1", 50, 0.0005),
        _span("t2", "Task: Estimate the budget", "general", "k"),
        _span("a2", "Budget Estimator", "general", "t2"),
        _span("l3", "chat_completion_create", "llm", "a2", 200, 0.002),
    ]
    totals = cost_by_agent(spans)
    assert totals["Scope Planner"] == {"tokens": 150, "cost": 0.0015}
    assert totals["Budget Estimator"] == {"tokens": 200, "cost": 0.002}
