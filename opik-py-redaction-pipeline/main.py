"""PII redaction pipeline: regex pre-pass -> LLM contextual pass -> verification."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
os.environ.setdefault("OPIK_PROJECT_NAME", "opik-py-redaction-pipeline")

import opik  # noqa: E402
from opik import id_helpers  # noqa: E402
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


def now() -> datetime:
    return datetime.now(timezone.utc)


def ask(client: OpenAI, system: str, text: str):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
    )
    return parse_json_object(response.choices[0].message.content), response


def traced_ask(opik_client, trace_id, parent_id, name, system, text, client):
    """One model call, recorded as an llm span with model, provider and token usage set by hand."""
    messages = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": text}]}
    start = now()
    parsed, response = ask(client, system, text)
    u = response.usage
    # type="llm" + model + provider + usage is what Opik prices: the token counts become the span's
    # usage columns and the server computes the estimated cost. Leave any of them out and the
    # span still appears, but with no cost. The span is sent once, already finished (start_time and
    # end_time given), because calling Span.end() right after creation can lose data when batching.
    opik_client.span(
        trace_id=trace_id,
        parent_span_id=parent_id,
        name=name,
        type="llm",
        start_time=start,
        end_time=now(),
        input=messages,
        output=parsed,
        model=response.model,
        provider="openai",
        usage={"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens, "total_tokens": u.total_tokens},
    )
    return parsed


def redact_document(opik_client: opik.Opik, client: OpenAI, doc: dict) -> dict:
    # Ids are generated up front so child spans can point at parents that are sent after them.
    trace_id = id_helpers.generate_id()
    trace_start = now()

    def step(name, type, start, step_id, input, output):
        # Sends one finished span under the trace. type="tool" is deterministic code, "general"
        # groups a step, "guardrail" is the check that decides whether the output may ship.
        opik_client.span(
            trace_id=trace_id, id=step_id, name=name, type=type,
            start_time=start, end_time=now(), input=input, output=output,
        )

    start = now()
    text, counts = regex_redact(doc["text"])
    step("regex-pass", "tool", start, id_helpers.generate_id(), {"text": doc["text"]}, {"text": text, "matches": counts})

    # The llm call is a child of the step span, so the tree reads step -> model call.
    start, step_id, before = now(), id_helpers.generate_id(), text
    found = traced_ask(opik_client, trace_id, step_id, "find-contextual-pii", FIND_SYSTEM, text, client)
    text, masked = apply_findings(text, found.get("findings", []))
    step("contextual-pass", "general", start, step_id, {"text": before}, {"text": text, "masked": masked})

    start, step_id, before = now(), id_helpers.generate_id(), text
    audit = traced_ask(opik_client, trace_id, step_id, "audit-redacted-text", AUDIT_SYSTEM, text, client)
    remaining = audit.get("remaining", []) + regex_rescan(text)
    text, extra = apply_findings(text, remaining)
    confidence = float(audit.get("confidence", 0))
    step("verify", "guardrail", start, step_id, {"text": before}, {"text": text, "masked": extra, "auditor_confidence": confidence})

    # client.trace() with an explicit id and end_time writes the root of the tree in one message,
    # in the project named by OPIK_PROJECT_NAME. Its output is the final redacted document.
    opik_client.trace(
        id=trace_id,
        name="redact-document",
        start_time=trace_start,
        end_time=now(),
        input={"document_id": doc["id"], "text": doc["text"]},
        output={"text": text},
        tags=[doc["id"]],
        metadata={"title": doc["title"], "model": MODEL},
    )

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
    opik_client = opik.Opik()
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)
    for doc in json.loads(DATA.read_text()):
        started = time.time()
        result = redact_document(opik_client, client, doc)
        (out_dir / f"{doc['id']}.txt").write_text(result["text"])
        print(f"\n=== {doc['title']} ({time.time() - started:.1f}s)")
        print(result["text"])
        print(
            f"-- regex {result['regex_counts']} | llm masked {result['llm_masked']} | "
            f"verify masked {result['verify_masked']} | confidence {result['confidence']:.2f} | "
            f"leaked {len(result['leaked'])} {result['leaked']}"
        )
    # flush() blocks until the background batch is delivered. A short script exits before the
    # sender thread runs, so without it the run prints results and Opik stays empty.
    opik_client.flush()


if __name__ == "__main__":
    main()
