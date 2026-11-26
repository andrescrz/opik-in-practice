"""One guest conversation: message history plus the model call."""

from concierge.config import MODEL


class Session:
    def __init__(self, client, system_prompt: str, session_id: str):
        self.client = client
        self.session_id = session_id
        self.messages = [{"role": "system", "content": system_prompt}]
        self.last_usage = None

    def ask(self, guest_message: str) -> str:
        self.messages.append({"role": "user", "content": guest_message})
        response = self.client.chat.completions.create(
            model=MODEL, messages=self.messages
        )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        self.last_usage = response.usage
        return reply
