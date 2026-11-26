import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_brief(path: Path = DATA_DIR / "brief.md") -> str:
    return path.read_text()


def load_price_sheet(path: Path = DATA_DIR / "price_sheet.csv") -> str:
    """Render the CSV as pipe-separated lines the agents can read."""
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    lines = ["item | unit | unit price (USD) | notes"]
    lines += [f"{r['item']} | {r['unit']} | {r['unit_price_usd']} | {r['notes']}" for r in rows]
    return "\n".join(lines)
