from typing_extensions import TypedDict


class Finding(TypedDict):
    question: str
    answer: str
    sources: list[str]


class PostmortemState(TypedDict):
    incident: str
    questions: list[str]
    findings: list[Finding]
    postmortem: str
