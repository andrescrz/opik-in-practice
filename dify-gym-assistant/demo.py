#!/usr/bin/env python3
"""Talk to the gym assistant through Dify's service API, the way a website chat
widget would: two members, each in their own conversation."""

import json
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
state = json.loads((HERE / ".dify-state.json").read_text())
CHAT_URL = state["dify_url"].rstrip("/") + "/v1/chat-messages"

MEMBERS = {
    "member-ana": [
        "I'm on the off-peak plan. Can I come to the Monday evening spin class?",
        "OK, how much more per month would Full cost me?",
        "And if I travel all of July, can I freeze instead of cancelling?",
    ],
    "member-raj": [
        "Can I bring my 15-year-old nephew on Saturday?",
        "My knee hurts after squats, what stretches should I do?",
    ],
}


def ask(user: str, question: str, conversation_id: str) -> dict:
    body = {"inputs": {}, "query": question, "user": user,
            "response_mode": "blocking", "conversation_id": conversation_id}
    req = urllib.request.Request(CHAT_URL, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {state['service_key']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    for user, questions in MEMBERS.items():
        print(f"=== {user}")
        conversation_id = ""
        for q in questions:
            reply = ask(user, q, conversation_id)
            conversation_id = reply["conversation_id"]
            usage = reply.get("metadata", {}).get("usage", {})
            print(f"> {q}\n{reply['answer']}\n  [{usage.get('total_tokens')} tokens]\n")
        print(f"conversation {conversation_id}\n")


if __name__ == "__main__":
    sys.exit(main())
