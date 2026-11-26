import json
from types import SimpleNamespace

import main


class StubOpenAI:
    """Answers the find call, then the audit call, with canned JSON and fixed usage."""

    def __init__(self, replies):
        self.replies = iter(replies)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        message = SimpleNamespace(content=json.dumps(next(self.replies)))
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage, model="gpt-4o-mini-stub")


class RecordingOpik:
    """Stands in for opik.Opik(): the low-level client ignores OPIK_TRACK_DISABLE, so unit tests
    pass a recorder instead of letting stub data reach a real project."""

    def __init__(self):
        self.spans, self.traces = [], []

    def span(self, **kwargs):
        self.spans.append(kwargs)

    def trace(self, **kwargs):
        self.traces.append(kwargs)
        return SimpleNamespace(log_feedback_score=lambda **kw: self.traces[-1].setdefault("scores", {}).update({kw["name"]: kw["value"]}))


DOC = {
    "id": "t",
    "title": "t",
    "text": "Mail ana@x.test. Ana Ruiz lives at 4 Elm Road and works at Calder Mills.",
    "pii": ["ana@x.test", "Ana Ruiz", "4 Elm Road", "Calder Mills"],
}


def test_traced_pipeline_records_the_span_tree():
    stub = StubOpenAI(
        [
            {"findings": [{"text": "Ana Ruiz", "type": "NAME"}, {"text": "4 Elm Road", "type": "ADDRESS"}]},
            {"remaining": [{"text": "Calder Mills", "type": "ORG"}], "confidence": 0.6},
        ]
    )
    recorder = RecordingOpik()
    result = main.redact_document(recorder, stub, DOC)
    assert result["text"] == "Mail [EMAIL]. [NAME] lives at [ADDRESS] and works at [ORG]."
    assert result["leaked"] == []
    assert result["verify_masked"] == 1
    assert result["confidence"] == 0.6

    types = {s["name"]: s["type"] for s in recorder.spans}
    assert types == {
        "regex-pass": "tool",
        "find-contextual-pii": "llm",
        "contextual-pass": "general",
        "audit-redacted-text": "llm",
        "verify": "guardrail",
    }
    llm = next(s for s in recorder.spans if s["name"] == "find-contextual-pii")
    assert llm["provider"] == "openai" and llm["usage"]["total_tokens"] == 15
    assert recorder.traces[0]["scores"] == {"redaction-confidence": 0.6, "leaked-pii-count": 0.0}


def test_a_missed_name_is_counted_as_a_leak():
    stub = StubOpenAI([{"findings": []}, {"remaining": [], "confidence": 0.95}])
    result = main.redact_document(RecordingOpik(), stub, DOC)
    assert sorted(result["leaked"]) == ["4 Elm Road", "Ana Ruiz", "Calder Mills"]
