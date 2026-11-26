import base64

from openai import OpenAI

MODEL = "gpt-image-1"
SIZE = "1024x1024"
QUALITY = "low"  # cheapest setting, plenty for a demo


def make_client() -> OpenAI:
    return OpenAI()


def generate_png(client: OpenAI, prompt: str) -> tuple[bytes, dict]:
    """Returns (png bytes, the Images API usage block as a dict)."""
    result = client.images.generate(model=MODEL, prompt=prompt, size=SIZE, quality=QUALITY, n=1)
    usage = result.usage.model_dump() if result.usage else {}
    return base64.b64decode(result.data[0].b64_json), usage
