from types import SimpleNamespace

import classify
from reviews import LABELS, REVIEWS


def fake_client(reply: str):
    def create(**kwargs):
        create.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])

    create.calls = []
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_normalize_unifies_separators_and_punctuation():
    assert classify.normalize(" 'Bug Report.' ") == "bug_report"
    assert classify.normalize("billing-complaint") == "billing_complaint"


def test_intent_match_rejects_extra_words():
    assert classify.intent_match("praise", "Praise") == 1.0
    assert classify.intent_match("praise", "praise - they love it") == 0.0


def test_classify_sends_system_prompt_and_review(monkeypatch):
    client = fake_client("bug_report")
    monkeypatch.setattr(classify, "get_client", lambda: client)
    # @track-decorated: runs normally with OPIK_TRACK_DISABLE=true and no Opik server
    assert classify.classify("It crashes", system="Be brief.") == "bug_report"
    sent = client.chat.completions.create.calls[0]["messages"]
    assert sent == [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "It crashes"},
    ]


def test_dataset_is_balanced_and_labels_are_known():
    assert len(REVIEWS) == 20
    counts = {label: 0 for label in LABELS}
    for _, label in REVIEWS:
        counts[label] += 1
    assert set(counts.values()) == {4}
