import json
from types import SimpleNamespace

import pytest

import main


def test_parse_triage_normalizes_urgency():
    raw = json.dumps({"caller": "A", "urgency": " Emergency "})
    assert main.parse_triage(raw)["urgency"] == "emergency"


def test_parse_triage_rejects_unknown_urgency():
    with pytest.raises(ValueError):
        main.parse_triage(json.dumps({"urgency": "whenever"}))


def test_callback_list_orders_by_urgency_and_is_stable():
    results = [
        {"id": "a", "urgency": "routine"},
        {"id": "b", "urgency": "emergency"},
        {"id": "c", "urgency": "urgent"},
        {"id": "d", "urgency": "emergency"},
    ]
    assert [r["id"] for r in main.build_callback_list(results)] == ["b", "d", "c", "a"]


def test_voicemail_scripts_are_complete():
    voicemails = main.load_voicemails()
    assert len(voicemails) >= 5
    assert all({"id", "caller", "voice", "script"} <= vm.keys() for vm in voicemails)
    assert len({vm["id"] for vm in voicemails}) == len(voicemails)


def test_traced_triage_runs_with_stubbed_client(monkeypatch):
    # With tracking disabled (OPIK_TRACK_DISABLE=true) @opik.track is a
    # pass-through, so the decorated function behaves like a plain one.
    reply = json.dumps({"caller": "Dana", "urgency": "urgent", "reason": "limping"})
    completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: completion))
    )
    monkeypatch.setattr(main, "get_client", lambda: client)
    assert main.triage("my cat is limping")["urgency"] == "urgent"
