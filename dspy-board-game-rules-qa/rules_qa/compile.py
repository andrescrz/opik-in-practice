import dspy

from .config import COMPILED_PATH
from .data import build_trainset
from .metric import format_and_citation
from .program import build_program


def compile_program() -> dspy.Module:
    # BootstrapFewShot runs the program over the trainset, keeps the attempts
    # that pass the metric (reasoning included) and bakes up to 4 of them
    # into the prompt as demos.
    optimizer = dspy.BootstrapFewShot(
        metric=format_and_citation,
        max_bootstrapped_demos=4,
        max_labeled_demos=4,
        max_rounds=1,
    )
    compiled = optimizer.compile(build_program(), trainset=build_trainset())
    COMPILED_PATH.parent.mkdir(exist_ok=True)
    compiled.save(COMPILED_PATH)
    return compiled
