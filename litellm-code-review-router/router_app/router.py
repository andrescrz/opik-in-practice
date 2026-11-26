"""Model routing: one function, any provider, via LiteLLM."""

import time
from dataclasses import dataclass

import litellm
import opik
from opik.opik_context import get_current_span_data

MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5-20251001",
]


@dataclass
class Call:
    model: str
    text: str
    latency_s: float
    cost_usd: float
    tokens: int


def short_name(model: str) -> str:
    return model.split("/", 1)[-1]


# @track opens one trace per (model, patch) call; the nested LiteLLM completion
# becomes an llm span under it, so each trace carries the model name, usage and cost.
@opik.track(name="route_review")
def route(model: str, messages: list[dict]) -> Call:
    start = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=messages,
        # Without current_span_data the LiteLLM callback can't see the active @track
        # span and the llm span lands as a separate, orphaned trace.
        metadata={"opik": {"current_span_data": get_current_span_data(), "tags": [short_name(model)]}},
    )
    latency = time.perf_counter() - start
    return Call(
        model=model,
        text=response.choices[0].message.content or "",
        latency_s=latency,
        cost_usd=response._hidden_params.get("response_cost") or 0.0,
        tokens=response.usage.total_tokens,
    )
