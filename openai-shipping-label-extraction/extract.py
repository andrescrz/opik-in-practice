"""Read one shipping-label image with gpt-4o-mini and return a typed LabelFields."""

import base64
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

load_dotenv(find_dotenv(usecwd=False))

from openai import OpenAI  # noqa: E402

HERE = Path(__file__).parent
MODEL = "gpt-4o-mini"

client = OpenAI()

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


def extract_label(image_path: str) -> LabelFields:
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
