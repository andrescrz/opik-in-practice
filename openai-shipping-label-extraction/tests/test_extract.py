from types import SimpleNamespace

import extract


def test_extract_label_runs_with_tracking_disabled(monkeypatch):
    """@opik.track and track_openai stay out of the way: the traced function is
    a plain call and returns the typed model from a stubbed client."""
    fields = extract.LabelFields(
        tracking_number="NW7741920385", carrier="Northwind Parcel", service_level="Ground",
        weight_kg=2.4, ship_to_name="Imogen Farrow", ship_to_postcode="40213",
    )
    seen = {}

    def fake_parse(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=fields))])

    monkeypatch.setattr(extract.client.chat.completions, "parse", fake_parse)

    result = extract.extract_label("data/label_01_clean_northwind.png")

    assert result == fields
    image_part = seen["messages"][1]["content"][1]
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    assert seen["response_format"] is extract.LabelFields
