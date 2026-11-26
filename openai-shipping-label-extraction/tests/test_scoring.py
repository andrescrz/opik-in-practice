from labels import LABELS
from scoring import accuracy, field_matches

EXPECTED = LABELS[0]["expected"]


def test_case_and_spacing_do_not_count():
    got = {**EXPECTED, "carrier": "NORTHWIND PARCEL", "tracking_number": "nw 7741-920385"}
    assert all(field_matches(got, EXPECTED).values())


def test_empty_string_never_matches():
    got = {**EXPECTED, "tracking_number": ""}
    assert field_matches(got, EXPECTED)["tracking_number"] is False


def test_weight_is_compared_numerically():
    assert field_matches({**EXPECTED, "weight_kg": 2.4000001}, EXPECTED)["weight_kg"]
    assert not field_matches({**EXPECTED, "weight_kg": 3.1}, EXPECTED)["weight_kg"]


def test_accuracy_averages_per_field():
    good = field_matches(EXPECTED, EXPECTED)
    bad = field_matches({**EXPECTED, "ship_to_postcode": "00000"}, EXPECTED)
    acc = accuracy([good, bad])
    assert acc["ship_to_postcode"] == 0.5 and acc["carrier"] == 1.0
