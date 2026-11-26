from types import SimpleNamespace

from parkguide.corpus import load_sections, split_markdown
from parkguide.evaluation import DATASET_ITEMS
from parkguide.graph import SYSTEM_PROMPT, build_graph
from parkguide.retriever import KeywordRetriever, tokenize


class StubLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return SimpleNamespace(content="stub answer")


def test_split_markdown_makes_one_section_per_heading():
    sections = split_markdown("demo", "# Title\n\n## One\nfirst\nline\n\n## Two\nsecond\n")
    assert [(s.heading, s.text) for s in sections] == [("One", "first line"), ("Two", "second")]


def test_guide_loads_all_four_pages():
    sections = load_sections()
    assert {s.source for s in sections} == {"trails", "permits", "campgrounds", "wildlife"}
    assert len(sections) == 16


def test_tokenize_drops_stopwords_and_plurals():
    assert tokenize("Are the dogs allowed?") == ["dog", "allowed"]


def test_retriever_ranks_the_matching_section_first():
    retriever = KeywordRetriever(load_sections())
    top = retriever.search("How much is a backcountry permit?", k=2)
    assert top[0].heading == "Overnight backcountry permits"


def test_retriever_returns_nothing_for_unknown_topics():
    assert KeywordRetriever(load_sections()).search("airport shuttle bus", k=4) == []


def test_traced_search_still_runs_with_tracking_disabled():
    # search() carries @opik.track; with tracking off it must behave like a plain method.
    results = KeywordRetriever(load_sections()).search("quiet hours", k=1)
    assert results[0].heading == "Fernwater Campground"


def test_graph_passes_retrieved_sections_to_the_model():
    llm = StubLLM()
    app = build_graph(KeywordRetriever(load_sections()), llm, k=2)
    result = app.invoke({"question": "Are dogs allowed on Ember Ridge?"})
    assert result["answer"] == "stub answer"
    assert len(result["context"]) == 2
    system_message = llm.messages[0][1]
    assert system_message.startswith(SYSTEM_PROMPT)
    assert "ground-nesting birds" in system_message


def test_dataset_items_have_question_and_reference_answer():
    assert len(DATASET_ITEMS) == 8
    assert all(item["question"] and item["expected_output"] for item in DATASET_ITEMS)
