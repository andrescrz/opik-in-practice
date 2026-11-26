import os

# extract.py builds its OpenAI client at import; the tests stub every call, so a dummy key is enough.
os.environ.setdefault("OPENAI_API_KEY", "not-a-real-key")
