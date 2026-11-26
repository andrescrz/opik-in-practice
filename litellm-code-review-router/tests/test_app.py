from router_app import router
from router_app.report import comparison_table
from router_app.reviewers import build_messages, load_patches
from router_app.router import Call


def test_patches_load_and_prompt_contains_diff():
    patches = load_patches()
    assert len(patches) == 5
    msgs = build_messages(patches[0])
    assert msgs[0]["role"] == "system" and patches[0]["diff"] in msgs[1]["content"]


def test_comparison_table_groups_by_model():
    calls = [
        Call("openai/gpt-4o-mini", "x", 1.0, 0.001, 100),
        Call("openai/gpt-4o-mini", "x", 3.0, 0.003, 200),
        Call("anthropic/claude-haiku-4-5-20251001", "x", 2.0, 0.01, 400),
    ]
    table = comparison_table(calls)
    assert "gpt-4o-mini" in table and "300" in table and "2.00s" in table
    assert "claude-haiku-4-5-20251001" in table and "0.010000" in table


def test_traced_route_runs_with_tracking_disabled(monkeypatch):
    class Resp:
        choices = [type("C", (), {"message": type("M", (), {"content": "ok"})()})()]
        usage = type("U", (), {"total_tokens": 7})()
        _hidden_params = {"response_cost": 0.5}

    monkeypatch.setattr(router.litellm, "completion", lambda **kw: Resp())
    call = router.route("openai/gpt-4o-mini", [{"role": "user", "content": "hi"}])
    assert (call.text, call.tokens, call.cost_usd) == ("ok", 7, 0.5)
