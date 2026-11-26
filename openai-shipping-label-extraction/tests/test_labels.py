from labels import DATA, LABELS, render
from main import TEST_ITEMS, assertions_for


def test_every_label_has_a_committed_image():
    for label in LABELS:
        assert (DATA / label["file"]).exists(), label["file"]


def test_rendering_is_deterministic():
    label = LABELS[6]
    assert render(label).tobytes() == render(label).tobytes()


def test_rotated_label_is_portrait():
    rotated = next(label for label in LABELS if label["damage"] == "rotate90")
    width, height = render(rotated).size
    assert height > width


def test_handwritten_label_differs_from_clean_render():
    label = next(label for label in LABELS if label["damage"] == "handwritten_weight")
    clean = render({**label, "damage": "clean", "expected": {**label["expected"], "weight_kg": 2.4}})
    assert render(label).tobytes() != clean.tobytes()


def test_assertions_carry_the_expected_values():
    label = LABELS[7]
    text = " ".join(assertions_for(label))
    assert label["expected"]["ship_to_postcode"] in text and label["expected"]["tracking_number"] in text
    assert len(TEST_ITEMS) == len(LABELS)
