"""Deterministic field-by-field comparison, independent of any LLM judge."""

import re

FIELDS = ("tracking_number", "carrier", "service_level", "weight_kg", "ship_to_name", "ship_to_postcode")


def _norm(value: object) -> str:
    return re.sub(r"[\s\-]+", "", str(value)).casefold()


def field_matches(got: dict, expected: dict) -> dict[str, bool]:
    """Case, spacing and dash differences don't count (the model upper-cases printed
    headers); weights must agree to 0.01 kg; an empty string never matches."""
    result = {}
    for name in FIELDS:
        if name == "weight_kg":
            result[name] = abs(float(got.get(name) or 0) - expected[name]) < 0.01
        else:
            result[name] = bool(got.get(name)) and _norm(got[name]) == _norm(expected[name])
    return result


def accuracy(matches: list[dict[str, bool]]) -> dict[str, float]:
    return {name: sum(m[name] for m in matches) / len(matches) for name in FIELDS}
