from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from smolagents import ChatMessage, Model

import main

REPLY = 'Thought: done.\n<code>\nfinal_answer("Array C")\n</code>'


class StubModel(Model):
    def generate(self, messages, **kwargs):
        return ChatMessage(role="assistant", content=REPLY)


def test_instrumented_agent_runs_offline(monkeypatch):
    # Instrumented with a provider that has no exporter: spans are created and dropped,
    # showing the instrumentation does not get in the way of unit tests.
    SmolagentsInstrumentor().instrument(tracer_provider=TracerProvider())
    monkeypatch.setattr(main, "OpenAIServerModel", lambda model_id: StubModel())
    agent = main.build_agent()
    assert agent.run(main.BRIEFING + main.QUESTIONS[0]) == "Array C"
    assert "pandas" in agent.authorized_imports
