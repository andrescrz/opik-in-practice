"""Read one shipping-label image with gpt-4o-mini and return a typed LabelFields."""

import base64
from pathlib import Path

import os

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

# Load .env first: Opik reads its URL, workspace and project name from the environment
# when the SDK is imported, so they must be set before that import.
load_dotenv(find_dotenv(usecwd=False))
PROJECT_NAME = "openai-shipping-label-extraction"
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from openai import OpenAI  # noqa: E402
from opik import Attachment, opik_context  # noqa: E402
from opik.integrations.openai import track_openai  # noqa: E402

HERE = Path(__file__).parent
MODEL = "gpt-4o-mini"

# track_openai wraps the client: every completion (including .parse) becomes an llm span
# nested under the active trace, with token usage and cost. Image input shows up in the span input.
client = track_openai(OpenAI(), project_name=PROJECT_NAME)

SYSTEM_PROMPT = """\
You read photos of parcel shipping labels and extract six fields. Read only what
is printed or handwritten on the label; never guess a value you cannot read.
If a printed value is struck out and a handwritten one is written beside it,
the handwritten value is the correct one. The label may be rotated or tilted.
If a field is unreadable, return an empty string (or 0 for the weight)."""


class LabelFields(BaseModel):
    tracking_number: str = Field(description="Tracking number exactly as printed, including spaces and dashes")
    carrier: str = Field(description="Carrier name from the header band")
    service_level: str = Field(description="Service level, e.g. Ground, Express, Next Day")
    weight_kg: float = Field(description="Parcel weight in kilograms")
    ship_to_name: str = Field(description="Recipient name in the SHIP TO block")
    ship_to_postcode: str = Field(description="Recipient postcode / ZIP as written")


# @opik.track makes each call one trace named extract_label (a general span) that holds the
# llm span below. Without it the completion would land as a bare, unnamed llm trace.
@opik.track(project_name=PROJECT_NAME)
def extract_label(image_path: str) -> LabelFields:
    # Attaching the PNG puts the exact pixels the model saw on the trace's Attachments tab,
    # next to the fields it claimed to read, so a wrong field can be judged against the image.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(HERE / image_path), content_type="image/png")]
    )
    image_b64 = base64.b64encode((HERE / image_path).read_bytes()).decode()
    response = client.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the fields from this shipping label."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                    },
                ],
            },
        ],
        response_format=LabelFields,
    )
    return response.choices[0].message.parsed
