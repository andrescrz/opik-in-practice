"""The three agents. Each takes the chat model as an argument so tests can stub it."""

from pydantic import BaseModel, Field

from .corpus import search
from .state import Finding, PostmortemState


class InvestigationPlan(BaseModel):
    """The planner's output: a few focused, answerable questions."""

    questions: list[str] = Field(
        description="3 to 4 questions that together explain the incident"
    )


def planner(state: PostmortemState, llm) -> dict:
    plan = llm.with_structured_output(InvestigationPlan).invoke([
        ("system",
         "You lead the investigation of a production outage. The evidence is a "
         "fixed set of artifacts: an incident timeline, alert history, "
         "service logs, chat excerpts from the incident channel, and process "
         "documents. Split the investigation into 3-4 concrete questions, each "
         "answerable from those artifacts. Cover: what changed and why, how "
         "detection worked, what slowed the response, and what made it worse."),
        ("user", state["incident"]),
    ])
    return {"questions": plan.questions, "findings": []}


def investigator(state: PostmortemState, llm, corpus: list[dict]) -> dict:
    """Answer the next open question from the best-matching artifact chunks."""
    question = state["questions"][len(state["findings"])]
    hits = search(question, corpus)
    excerpts = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    answer = llm.invoke([
        ("system",
         "You are an incident investigator. Answer the question using only "
         "the artifact excerpts below. Quote times and numbers, and name the "
         "source file for each claim. If the excerpts do not say, say so.\n\n"
         + excerpts),
        ("user", question),
    ])
    finding: Finding = {
        "question": question,
        "answer": answer.content,
        "sources": sorted({h["source"] for h in hits}),
    }
    return {"findings": state["findings"] + [finding]}


def route_investigation(state: PostmortemState) -> str:
    """Loop the investigator until every question has a finding."""
    if len(state["findings"]) < len(state["questions"]):
        return "investigator"
    return "writer"


def writer(state: PostmortemState, llm) -> dict:
    notes = "\n\n".join(
        f"### {f['question']}\n{f['answer']}\n(Sources: {', '.join(f['sources'])})"
        for f in state["findings"]
    )
    draft = llm.invoke([
        ("system",
         "You write blameless post-mortems. Sections: Summary, Impact, "
         "Timeline, Contributing factors, What went well, Action items. "
         "Describe systems and processes, never blame individuals (refer to "
         "roles such as 'the on-call engineer'). Use only the notes below and "
         "keep every time, number and source accurate. Under 500 words.\n\n"
         + notes),
        ("user", state["incident"]),
    ])
    return {"postmortem": draft.content}
