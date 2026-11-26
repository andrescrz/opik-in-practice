import re

# The required answer format: one trailing section citation like "[§2.2]".
CITATION = re.compile(r"\[§(\d+\.\d+)\]\s*$")


def cited_section(answer: str) -> str | None:
    match = CITATION.search(answer.strip())
    return match.group(1) if match else None


def format_and_citation(example, prediction, trace=None) -> bool:
    """Compile-time metric: trailing citation, correct section, key fact present.

    Purely programmatic, so compiling spends no judge tokens.
    """
    answer = prediction.answer.strip()
    if cited_section(answer) != example.section:
        return False
    return example.key_fact.lower() in answer.lower()
