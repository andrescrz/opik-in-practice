"""Boot the chat API in-process, play three scripted patron conversations, and exit."""

import opik
from fastapi.testclient import TestClient

from librarian.app import app

CONVERSATIONS = {
    "patron-cozy-coastal": [
        "I loved quiet mysteries by the sea. What should I read next?",
        "Something shorter, with a bit of a puzzle in it.",
        "Is the first one you mentioned on the shelf right now?",
    ],
    "patron-teen-sci-fi": [
        "My niece is into gentle science fiction with robots. Any ideas?",
        "She only has a weekend. Which of those is the quickest read?",
        "Great. Do you have anything about dragons for me, for something funny?",
    ],
    "patron-travel-nonfiction": [
        "I want true stories about travel and nature, with some humour.",
        "Anything that also feels hopeful rather than bleak?",
    ],
}


def main() -> None:
    with TestClient(app) as client:
        for session_id, turns in CONVERSATIONS.items():
            print(f"\n=== {session_id} ===")
            for message in turns:
                reply = client.post("/chat", json={"message": message, "session_id": session_id}).json()["reply"]
                print(f"patron: {message}\nlibrary: {reply}\n")
    # Traces are sent in the background; flush so none are lost when the process exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
