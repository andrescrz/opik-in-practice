"""Fictional shipping labels, drawn deterministically with Pillow.

LABELS is the single source of truth: each entry says what is printed on the
label (`expected`) and how the image gets damaged (`damage`). `python labels.py`
regenerates data/*.png, which are committed so the run never depends on drawing.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
DATA = HERE / "data"
W, H = 640, 420

LABELS = [
    {
        "file": "label_01_clean_northwind.png",
        "damage": "clean",
        "note": "Clean print, upright.",
        "expected": {
            "tracking_number": "NW7741920385", "carrier": "Northwind Parcel",
            "service_level": "Ground", "weight_kg": 2.4,
            "ship_to_name": "Imogen Farrow", "ship_to_postcode": "40213",
        },
        "from": "Tidewater Candle Co., Port Alder",
    },
    {
        "file": "label_02_clean_kestrel.png",
        "damage": "clean",
        "note": "Clean print, upright, UK-style postcode.",
        "expected": {
            "tracking_number": "KP 5530 8841 26", "carrier": "Kestrel Post",
            "service_level": "Next Day", "weight_kg": 0.8,
            "ship_to_name": "Dev Ramaswamy", "ship_to_postcode": "BN7 2QX",
        },
        "from": "Lantern & Loom, Hollowby",
    },
    {
        "file": "label_03_clean_swiftarrow.png",
        "damage": "clean",
        "note": "Clean print, upright, heavy parcel.",
        "expected": {
            "tracking_number": "SA-902117-4466", "carrier": "SwiftArrow Express",
            "service_level": "Priority", "weight_kg": 12.75,
            "ship_to_name": "Marguerite Oyelaran", "ship_to_postcode": "98104",
        },
        "from": "Brightfield Cycles, Ostrava Bay",
    },
    {
        "file": "label_04_rotated_90.png",
        "damage": "rotate90",
        "note": "Whole label photographed sideways (rotated 90 degrees).",
        "expected": {
            "tracking_number": "NW3308157720", "carrier": "Northwind Parcel",
            "service_level": "Express", "weight_kg": 5.2,
            "ship_to_name": "Tomasz Wieland", "ship_to_postcode": "60614",
        },
        "from": "Alder Press, Fenwick",
    },
    {
        "file": "label_05_tilted_crumpled.png",
        "damage": "tilt",
        "note": "Tilted about 14 degrees with a dark paper edge and noise.",
        "expected": {
            "tracking_number": "KP 1187 6403 92", "carrier": "Kestrel Post",
            "service_level": "Standard", "weight_kg": 1.35,
            "ship_to_name": "Saoirse Lindqvist", "ship_to_postcode": "M4 5JD",
        },
        "from": "Wren & Thistle, Calder Vale",
    },
    {
        "file": "label_06_smudged_tracking.png",
        "damage": "smudge",
        "note": "Wet smear across the tracking number and the barcode.",
        "expected": {
            "tracking_number": "SA-440823-9015", "carrier": "SwiftArrow Express",
            "service_level": "Priority", "weight_kg": 3.9,
            "ship_to_name": "Kofi Brennan-Aaltonen", "ship_to_postcode": "30318",
        },
        "from": "Quillon Audio, Marrow Point",
    },
    {
        "file": "label_07_handwritten_weight.png",
        "damage": "handwritten_weight",
        "note": "Printed weight 2.4 kg struck out; handwritten correction reads 3.1.",
        "expected": {
            "tracking_number": "NW6620948113", "carrier": "Northwind Parcel",
            "service_level": "Ground", "weight_kg": 3.1,
            "ship_to_name": "Odalys Pemberton", "ship_to_postcode": "73301",
        },
        "from": "Kiln & Kettle Studio, Dunmore",
    },
    {
        "file": "label_08_handwritten_postcode.png",
        "damage": "handwritten_postcode",
        "note": "Printed postcode struck out; handwritten correction reads SE15 4TY.",
        "expected": {
            "tracking_number": "KP 7094 2215 58", "carrier": "Kestrel Post",
            "service_level": "Next Day", "weight_kg": 0.45,
            "ship_to_name": "Henrik Abara", "ship_to_postcode": "SE15 4TY",
        },
        "from": "Saltmarsh Books, Wickerby",
    },
    {
        "file": "label_09_lowres_blur.png",
        "damage": "lowres",
        "note": "Tiny, blurry thumbnail of a clean label (about 25% scale).",
        "expected": {
            "tracking_number": "SA-118305-2278", "carrier": "SwiftArrow Express",
            "service_level": "Standard", "weight_kg": 6.0,
            "ship_to_name": "Beatriz Okonkwo", "ship_to_postcode": "02139",
        },
        "from": "Harlow Ceramics, Teasel Cove",
    },
]

# Printed wrong on purpose, before the handwritten correction is added.
PRINTED_WRONG = {"weight_kg": 2.4, "ship_to_postcode": "SE15 4TR"}


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


def _fmt_weight(w: float) -> str:
    return f"{w:g} KG"


def _draw_label(label: dict) -> Image.Image:
    e = label["expected"]
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, W - 5, H - 5], outline="black", width=3)

    d.rectangle([4, 4, W - 5, 62], fill="black")
    d.text((22, 14), e["carrier"].upper(), font=_font(34), fill="white")
    d.text((W - 170, 20), e["service_level"].upper(), font=_font(26), fill="white")

    d.text((22, 74), "FROM:", font=_font(14), fill="black")
    d.text((22, 92), label["from"], font=_font(17), fill="black")
    d.line([(4, 124), (W - 5, 124)], fill="black", width=2)

    postcode = e["ship_to_postcode"]
    weight = _fmt_weight(e["weight_kg"])
    if label["damage"] == "handwritten_weight":
        weight = _fmt_weight(PRINTED_WRONG["weight_kg"])
    if label["damage"] == "handwritten_postcode":
        postcode = PRINTED_WRONG["ship_to_postcode"]

    d.text((22, 134), "SHIP TO:", font=_font(16), fill="black")
    d.text((22, 156), e["ship_to_name"].upper(), font=_font(32), fill="black")
    d.text((22, 198), "Dock 4, Receiving Hall", font=_font(20), fill="black")
    d.text((22, 226), postcode, font=_font(38), fill="black")

    d.text((W - 190, 134), "WEIGHT", font=_font(16), fill="black")
    d.text((W - 190, 158), weight, font=_font(34), fill="black")

    d.line([(4, 282), (W - 5, 282)], fill="black", width=2)
    rng = random.Random(e["tracking_number"])
    x = 28
    while x < W - 40:
        bw = rng.choice([2, 3, 4, 6])
        d.rectangle([x, 292, x + bw, 352], fill="black")
        x += bw + rng.choice([2, 3, 4])
    d.text((28, 362), "TRACKING " + e["tracking_number"], font=_font(30), fill="black")
    return img


def _handwrite(img: Image.Image, text: str, xy: tuple[int, int], size: int, seed: int) -> None:
    """Jittered, slightly rotated glyphs in blue ink, so it reads as a pen scrawl."""
    rng = random.Random(seed)
    x, y = xy
    font = _font(size)
    for ch in text:
        tile = Image.new("RGBA", (size + 10, size + 14), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((4, 2), ch, font=font, fill=(25, 40, 160, 255))
        tile = tile.rotate(rng.uniform(-14, 14), resample=Image.BICUBIC, expand=True)
        img.paste(tile, (x, y + rng.randint(-4, 5)), tile)
        x += int(size * 0.55) + rng.randint(0, 3)


def _strike(img: Image.Image, box: tuple[int, int, int, int]) -> None:
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.line([(x0, (y0 + y1) // 2 + 3), (x1, (y0 + y1) // 2 - 4)], fill=(25, 40, 160), width=4)


def _noise(img: Image.Image, amount: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    px = img.load()
    for _ in range(amount):
        x, y = rng.randrange(img.width), rng.randrange(img.height)
        v = rng.randint(90, 200)
        px[x, y] = (v, v, v)
    return img


def render(label: dict) -> Image.Image:
    img = _draw_label(label)
    damage = label["damage"]
    if damage == "handwritten_weight":
        _strike(img, (W - 190, 158, W - 70, 196))
        _handwrite(img, "3.1", (W - 190, 204), 40, seed=7)
    elif damage == "handwritten_postcode":
        _strike(img, (22, 226, 190, 266))
        _handwrite(img, "SE15 4TY", (22, 270), 34, seed=11)
    elif damage == "rotate90":
        img = img.rotate(90, expand=True, fillcolor="white")
    elif damage == "tilt":
        img = _noise(img, 250, seed=3)
        img = img.rotate(14, expand=True, fillcolor=(60, 55, 50), resample=Image.BICUBIC)
        img = img.resize((W, int(img.height * W / img.width))).quantize(colors=24)
    elif damage == "smudge":
        smear = img.crop((20, 286, W - 20, 400)).filter(ImageFilter.GaussianBlur(9))
        img.paste(smear, (20, 286))
        d = ImageDraw.Draw(img, "RGBA")
        d.polygon([(30, 340), (W - 30, 318), (W - 30, 372), (30, 394)], fill=(120, 120, 120, 110))
        img = _noise(img, 3000, seed=5)
    elif damage == "lowres":
        img = img.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8))
        img = img.resize((W // 2, H // 2), Image.BILINEAR)
    return img


def main() -> None:
    DATA.mkdir(exist_ok=True)
    for label in LABELS:
        render(label).save(DATA / label["file"], optimize=True)
    print(f"wrote {len(LABELS)} labels to {DATA}")


if __name__ == "__main__":
    main()
