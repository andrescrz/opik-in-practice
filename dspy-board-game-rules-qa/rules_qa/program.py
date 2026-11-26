import dspy

from .config import MODEL
from .rulebook import load_rulebook
from .signatures import RulesQuestion


def setup_dspy() -> None:
    dspy.configure(lm=dspy.LM(MODEL, cache=False))


def build_program() -> dspy.Module:
    return dspy.ChainOfThought(RulesQuestion)


def answer(program: dspy.Module, question: str) -> str:
    return program(rulebook=load_rulebook(), question=question).answer
