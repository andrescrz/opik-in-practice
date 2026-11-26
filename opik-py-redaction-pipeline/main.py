"""PII redaction pipeline: regex pre-pass -> LLM contextual pass -> verification."""
import json
import os
import time
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
os.environ.setdefault("OPIK_PROJECT_NAME", "opik-py-redaction-pipeline")

from openai import OpenAI  # noqa: E402

from redact import (  # noqa: E402
    apply_findings,
    leaked,
    parse_json_object,
    regex_redact,
    regex_rescan,
)

MODEL = "gpt-4o-mini"
DATA = Path(__file__).parent / "data" / "documents.json"

FIND_SYSTEM = (
    "You find personal data in a document that has already had emails, phones, SSNs and ID numbers masked. "
    "List every remaining string that identifies a real person or place: full or partial names, street "
    "addresses and unit numbers, employers, clinics, surgeries, and nicknames. Each string must be a short "
    "span (a name, an address, an organisation), never a whole sentence, copied EXACTLY as it appears. "
    'Reply with JSON only: {"findings": [{"text": "...", "type": "NAME|ADDRESS|ORG"}]}'
)
AUDIT_SYSTEM = (
    "You audit a redacted document for leftover personal data. List every string that still identifies a "
    "person, address, employer or clinic, as a short span copied exactly. Bracketed placeholders such as "
    "[NAME], [EMAIL] or [ADDRESS] are the correct result: they are not personal data and must never be "
    "listed. Then give a confidence from 0 to 1 that the document is safe to publish: 0.9 or more when you "
    "found nothing, lower for each string you found. "
    'Reply with JSON only: {"remaining": [{"text": "...", "type": "NAME|ADDRESS|ORG"}], "confidence": 0.0}'
)


def ask(client: OpenAI, system: str, text: str):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
    )
    return parse_json_object(response.choices[0].message.content), response


def redact_document(client: OpenAI, doc: dict) -> dict:
    text, counts = regex_redact(doc["text"])

    found, _ = ask(client, FIND_SYSTEM, text)
    text, masked = apply_findings(text, found.get("findings", []))

    audit, _ = ask(client, AUDIT_SYSTEM, text)
    remaining = audit.get("remaining", []) + regex_rescan(text)
    text, extra = apply_findings(text, remaining)
    confidence = float(audit.get("confidence", 0))

    return {
        "text": text,
        "regex_counts": counts,
        "llm_masked": masked,
        "verify_masked": extra,
        "confidence": confidence,
        "leaked": leaked(text, doc["pii"]),
    }


def main() -> None:
    client = OpenAI()
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)
    for doc in json.loads(DATA.read_text()):
        started = time.time()
        result = redact_document(client, doc)
        (out_dir / f"{doc['id']}.txt").write_text(result["text"])
        print(f"\n=== {doc['title']} ({time.time() - started:.1f}s)")
        print(result["text"])
        print(
            f"-- regex {result['regex_counts']} | llm masked {result['llm_masked']} | "
            f"verify masked {result['verify_masked']} | confidence {result['confidence']:.2f} | "
            f"leaked {len(result['leaked'])} {result['leaked']}"
        )


if __name__ == "__main__":
    main()
