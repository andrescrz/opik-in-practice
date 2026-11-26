import dspy
import opik
from opik.integrations.dspy.callback import OpikCallback

from .config import MODEL, PROJECT_NAME
from .rulebook import load_rulebook
from .signatures import RulesQuestion


def setup_dspy() -> None:
    # OpikCallback hooks DSPy's callback system: each module call becomes a
    # span (ChainOfThought > Predict > LM) with token usage and cost on the
    # LM span. log_graph=True also stores the module graph on the trace, so
    # the Opik UI can draw the program. Without it, DSPy runs but nothing
    # reaches Opik.
    dspy.configure(
        lm=dspy.LM(MODEL, cache=False),
        callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)],
    )


def build_program() -> dspy.Module:
    return dspy.ChainOfThought(RulesQuestion)


# @opik.track opens a "general" span around the DSPy call, so every DSPy
# trace has a named root ("answer") with the question and answer as I/O.
@opik.track(name="answer", type="general", project_name=PROJECT_NAME)
def answer(program: dspy.Module, question: str) -> str:
    return program(rulebook=load_rulebook(), question=question).answer
