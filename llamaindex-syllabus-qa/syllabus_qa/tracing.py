import opik
from llama_index.core import set_global_handler


def enable() -> None:
    # Registers Opik's LlamaIndex callback: every query becomes one trace, with retrieve
    # (embedding) and synthesize (chunking, templating, llm) spans, token usage and cost.
    # Without it LlamaIndex runs fine but nothing reaches Opik.
    set_global_handler("opik")


def flush() -> None:
    # Traces are sent from a background thread; a short CLI process would exit before they ship.
    opik.flush_tracker()
