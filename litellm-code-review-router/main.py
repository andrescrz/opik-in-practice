"""CLI: review every patch with every model and print the comparison table."""

import logging
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env (walking up from this folder) before any Opik or LiteLLM import,
# so OPIK_URL_OVERRIDE / OPIK_WORKSPACE override ~/.opik.config.
load_dotenv(find_dotenv(usecwd=False) or Path(__file__).resolve().parent.parent / ".env")
# Every trace from this app lands in this Opik project.
os.environ["OPIK_PROJECT_NAME"] = "litellm-code-review-router"

import litellm  # noqa: E402
import opik  # noqa: E402
from litellm.integrations.opik.opik import OpikLogger  # noqa: E402

from router_app.reviewers import build_messages, load_patches  # noqa: E402
from router_app.report import comparison_table  # noqa: E402
from router_app.router import MODELS, route  # noqa: E402

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
# OpikLogger turns every litellm.completion into an Opik llm span with usage and cost.
litellm.callbacks = [OpikLogger()]


def main() -> None:
    calls = []
    for patch in load_patches():
        for model in MODELS:
            call = route(model, build_messages(patch))
            calls.append(call)
            print(f"[{patch['id']:<15}] {model.split('/')[-1]:<28} {call.latency_s:5.2f}s  "
                  f"${call.cost_usd:.6f}  {call.text.splitlines()[0][:70]}")
    print()
    print(comparison_table(calls))
    # Traces are sent in the background; flush so none are lost when the process exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
