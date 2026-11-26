"""FastAPI chat endpoint: POST /chat {message, session_id} -> {reply}."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
import opik
from fastapi import FastAPI
from opik.integrations.langchain import OpikTracer
from pydantic import BaseModel, Field

# Load .env before anything reads the environment (walks up from this folder).
load_dotenv(find_dotenv(usecwd=False) or Path(__file__).resolve().parent.parent / ".env")

from librarian.chat import build_chain, remember  # noqa: E402

PROJECT_NAME = "langchain-fastapi-library-recs"
# Default project for @opik.track spans too, so tool spans never drift to "Default Project".
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

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
    # thread_id = session_id groups every turn of a session into one Opik thread; the tracer
    # turns each chain run, prompt, LLM call and parser into spans with token usage and cost.
    tracer = OpikTracer(project_name=PROJECT_NAME, thread_id=req.session_id)
    reply = get_chain().invoke(
        req.message,
        config={
            "configurable": {"session_id": req.session_id},
            "run_name": "library-chat-turn",
            "callbacks": [tracer],
        },
    )
    remember(req.session_id, req.message, reply)
    return ChatResponse(reply=reply)
