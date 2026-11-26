import base64
import os
from pathlib import Path

import opik
from openai import OpenAI

# gpt-image-1 is no longer served to every account ("The model `gpt-image-1` does not
# exist"), so the default is its cheaper successor; set IMAGE_MODEL to try another.
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1-mini")
SIZE = "1024x1024"
QUALITY = "low"  # cheapest setting, plenty for a demo


def make_client() -> OpenAI:
    # track_openai does not cover images.generate, so the call is traced by hand below.
    return OpenAI()


# type="llm" makes this an llm span (model, provider and usage columns); without
# the decorator the image call would not appear in Opik at all.
@opik.track(name="images.generate", type="llm")
def generate_png(client: OpenAI, prompt: str) -> bytes:
    result = client.images.generate(model=MODEL, prompt=prompt, size=SIZE, quality=QUALITY, n=1)
    png = base64.b64decode(result.data[0].b64_json)
    usage = result.usage
    # Log model, provider and the token usage the Images API reports so the span
    # can be priced. The raw base64 is deliberately not returned as the span
    # output: the PNG goes on the trace as an attachment instead.
    opik.opik_context.update_current_span(
        input={"prompt": prompt, "size": SIZE, "quality": QUALITY},
        output={"image_bytes": len(png)},
        model=MODEL,
        provider="openai",
        usage={
            "prompt_tokens": usage.input_tokens,
            "completion_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
        if usage
        else None,
    )
    return png


# Root function = one trace per illustration, named so the traces list reads as pages.
@opik.track(name="illustrate-page")
def illustrate(client: OpenAI, brief: opik.Prompt, scene: dict, out_dir: Path) -> Path:
    # Prompt.format insists on exactly the template's placeholders, so the scene's
    # extra "id" field must be dropped or it raises PromptPlaceholdersDontMatchFormatArguments.
    fields = {k: v for k, v in scene.items() if k != "id"}
    prompt = brief.format(**fields)
    png = generate_png(client, prompt)
    path = out_dir / f"{brief.version}-{scene['id']}.png"
    path.write_bytes(png)
    # Attachment uploads the file with the trace, so the Attachments tab shows
    # the actual picture next to the brief that produced it. prompts= links the
    # trace to the library version (the prompt shows on the trace and the
    # version's page lists its traces). Tags and metadata make versions filterable.
    opik.opik_context.update_current_trace(
        input={"scene_id": scene["id"], "page": scene["page"], "prompt": prompt},
        output={"image_file": path.name, "prompt_version": brief.version},
        attachments=[
            opik.Attachment(data=str(path), content_type="image/png", file_name=path.name)
        ],
        prompts=[brief],
        tags=[brief.version, scene["id"]],
        metadata={"prompt_version": brief.version, "model": MODEL},
    )
    return path
