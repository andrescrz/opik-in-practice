import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from librarian import app as app_module
from librarian import chat
from librarian.catalog import format_books, load_catalog, search_catalog


@pytest.fixture(autouse=True)
def fresh_sessions():
    chat.SESSIONS.clear()
    yield
    chat.SESSIONS.clear()


def test_catalog_has_unique_ids_and_required_fields():
    books = load_catalog()
    assert len({b["id"] for b in books}) == len(books) >= 20
    assert all({"title", "author", "tags", "copies_available"} <= b.keys() for b in books)


def test_search_prefers_tag_matches_and_ignores_filler_words():
    top = search_catalog("I want a gentle science fiction story with robots", k=2)
    assert top[0]["title"] == "Quiet Machines"
    assert search_catalog("zzz qqq") == []


def test_format_books_flags_out_of_stock_titles():
    out_of_stock = next(b for b in load_catalog() if b["copies_available"] == 0)
    assert "holds open" in format_books([out_of_stock])
    assert format_books([]) == "(no catalog matches)"


def test_traced_retrieval_runs_normally_with_tracking_disabled():
    # @opik.track must not change what the function returns, so unit tests need no Opik server.
    assert "Quiet Machines" in chat.retrieve_books("robots on a ship")


def test_chat_endpoint_is_string_in_string_out_and_remembers_turns(monkeypatch):
    fake = FakeListChatModel(responses=["Try Quiet Machines.", "It is 236 pages."])
    monkeypatch.setattr(app_module, "_chain", chat.build_chain(fake))
    client = TestClient(app_module.app)

    first = client.post("/chat", json={"message": "gentle robots?", "session_id": "s1"})
    second = client.post("/chat", json={"message": "how long is it?", "session_id": "s1"})

    assert first.json() == {"reply": "Try Quiet Machines."}
    assert second.json() == {"reply": "It is 236 pages."}
    assert len(chat.SESSIONS["s1"]) == 4
    assert "s2" not in chat.SESSIONS


def test_chat_rejects_empty_message():
    client = TestClient(app_module.app)
    assert client.post("/chat", json={"message": "", "session_id": "s1"}).status_code == 422
