"""Offline tests: no provider keys, no Opik server. Run with OPIK_TRACK_DISABLE=true."""

import types

import pypdf

from syllabus_qa import engine, pdfgen, questions, suite, tracing


def test_generate_writes_readable_pdfs(tmp_path):
    paths = pdfgen.generate_all(tmp_path)
    assert len(paths) == 3
    text = "".join(page.extract_text() for page in pypdf.PdfReader(paths[0]).pages)
    assert "Grading Policy" in text and "Office Hours" in text


def test_ask_returns_answer_and_sources():
    node = types.SimpleNamespace(text="Labs lose 10%.", metadata={"file_name": "cs210.pdf"})

    class Resp:
        source_nodes = [node]

        def __str__(self):
            return "ten percent"

    class Eng:
        def query(self, prompt):
            assert "Question: late labs?" in prompt and prompt.startswith(engine.GUIDANCE)
            return Resp()

    result = engine.ask(Eng(), "late labs?")
    assert result == {"answer": "ten percent", "sources": [{"file": "cs210.pdf", "text": "Labs lose 10%."}]}


def test_suite_items_are_well_formed():
    assert len(suite.ITEMS) >= 8
    assert {i["section"] for i in suite.ITEMS} >= {"grading", "late work", "office hours", "prerequisites"}
    assert all(i["assertions"] and i["question"] for i in suite.ITEMS)
    assert set(questions.DEMO_QUESTIONS) <= {i["question"] for i in suite.ITEMS}


def test_summarize_groups_pass_rate_by_section(capsys):
    def item(section, passed):
        case = types.SimpleNamespace(task_output={"input": {"section": section, "question": "q"}})
        run = types.SimpleNamespace(test_case=case, score_results=[])
        return types.SimpleNamespace(passed=passed, test_results=[run])

    result = types.SimpleNamespace(
        pass_rate=2 / 3, items_passed=2, items_total=3, experiment_url=None,
        item_results={"a": item("grading", True), "b": item("grading", False), "c": item("late work", True)},
    )
    assert suite.summarize(result) == {"grading": [True, False], "late work": [True]}
    assert "grading: 1/2" in capsys.readouterr().out


def test_tracing_helpers_are_harmless_when_tracking_is_disabled():
    tracing.enable()
    tracing.flush()
