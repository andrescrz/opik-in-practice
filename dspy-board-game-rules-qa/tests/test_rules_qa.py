import dspy

from rules_qa.data import TEST, TRAIN, build_trainset
from rules_qa.metric import cited_section, format_and_citation
from rules_qa.program import answer
from rules_qa.rulebook import load_rulebook, section_ids


def test_rulebook_sections_are_parsed():
    ids = section_ids(load_rulebook())
    assert ids[0] == "1.1" and "4.3" in ids and len(ids) == 11


def test_every_example_points_at_a_real_section():
    ids = set(section_ids(load_rulebook()))
    assert {section for _, _, section, _ in TRAIN} <= ids
    assert {section for _, section, _ in TEST} <= ids


def test_house_answers_pass_their_own_metric():
    for example in build_trainset():
        assert format_and_citation(example, dspy.Prediction(answer=example.answer))


def test_metric_rejects_prose_and_wrong_section():
    example = build_trainset()[2]
    assert not format_and_citation(example, dspy.Prediction(answer="The hand limit is 7 cards."))
    assert not format_and_citation(example, dspy.Prediction(answer="7 cards [§2.3]"))
    assert cited_section("7 cards [§2.2]  ") == "2.2"
    assert cited_section("see [§2.2] for details") is None


def test_traced_answer_runs_with_tracking_disabled():
    class StubProgram:
        def __call__(self, rulebook, question):
            assert "Lanternfall" in rulebook
            return dspy.Prediction(answer="1 oil token [§2.3]")

    assert answer(StubProgram(), "What does a bridge cost?") == "1 oil token [§2.3]"
