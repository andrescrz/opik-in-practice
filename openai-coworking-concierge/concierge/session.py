"""One guest conversation: message history plus the model call."""

import opik
from opik import opik_context

from concierge.config import MODEL


class Session:
    def __init__(self, client, system_prompt: str, session_id: str):
        self.client = client
        self.session_id = session_id
        self.messages = [{"role": "system", "content": system_prompt}]
        self.last_usage = None
        self.last_trace_id = None

    # One trace per guest turn; the llm span from track_openai nests inside it.
    @opik.track(name="concierge-turn")
    def ask(self, guest_message: str) -> str:
        self.messages.append({"role": "user", "content": guest_message})
        response = self.client.chat.completions.create(
            model=MODEL, messages=self.messages
        )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        self.last_usage = response.usage

        # thread_id is what groups the turns of one guest into a single
        # conversation in Opik's Threads tab; without it each turn is an orphan trace.
        opik_context.update_current_trace(thread_id=self.session_id)
        # With tracking disabled (e.g. unit tests) there is no current trace.
        trace = opik_context.get_current_trace_data()
        self.last_trace_id = trace.id if trace else None
        return reply
