"""Pure redaction logic: no model calls, no Opik."""
import json
import re

REGEX_RULES = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "PHONE": re.compile(r"(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-.]\d{4}\b"),
    "ID": re.compile(r"\b(?:MRN|LSE|PCC)-[\d-]+\b"),
    "DOB": re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
}


def regex_redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for label, pattern in REGEX_RULES.items():
        text, n = pattern.subn(f"[{label}]", text)
        if n:
            counts[label] = n
    return text, counts


def regex_rescan(text: str) -> list[str]:
    """Anything a regex rule still matches in already-redacted text."""
    return [m for pattern in REGEX_RULES.values() for m in pattern.findall(text)]


def apply_findings(text: str, findings: list, default_type: str = "REDACTED") -> tuple[str, int]:
    """Mask each finding that literally appears in the text. A finding is a string or
    {"text": ..., "type": ...}. Longest first, so 'Daniel A. Okonkwo' goes before 'Daniel'.
    Placeholders and sentence-length spans are skipped: a model that returns
    '[EMAIL]' or half the document would otherwise destroy the output."""
    items = {}
    for f in findings:
        value, kind = (f.get("text"), f.get("type")) if isinstance(f, dict) else (f, None)
        value = (value or "").strip()
        if not value or "[" in value or len(value.split()) > 10:
            continue
        items[value] = re.sub(r"\W", "", (kind or default_type).upper()) or default_type
    masked = 0
    for value in sorted(items, key=len, reverse=True):
        if value in text:
            text = text.replace(value, f"[{items[value]}]")
            masked += 1
    return text, masked


def leaked(text: str, known_pii: list[str]) -> list[str]:
    return [p for p in known_pii if p in text]


def parse_json_object(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)
