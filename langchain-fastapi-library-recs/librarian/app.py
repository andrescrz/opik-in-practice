"""FastAPI chat endpoint: POST /chat {message, session_id} -> {reply}."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Load .env before anything reads the environment (walks up from this folder).
load_dotenv(find_dotenv(usecwd=False) or Path(__file__).resolve().parent.parent / ".env")

from librarian.chat import build_chain, remember  # noqa: E402

PROJECT_NAME = "langchain-fastapi-library-recs"

app = FastAPI(title="Alder Creek Library Chat")
_chain = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str


def get_chain():
    global _chain
    if _chain is None:
        _chain = build_chain()
    return _chain


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    reply = get_chain().invoke(
        req.message,
        config={"configurable": {"session_id": req.session_id}, "run_name": "library-chat-turn"},
    )
    remember(req.session_id, req.message, reply)
    return ChatResponse(reply=reply)
