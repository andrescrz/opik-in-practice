"""LLM-judge test suite for the triage step.

Triage mistakes are asymmetric: calling a poisoned dog "routine" is far worse
than the reverse. The suite replays each transcript from out/transcripts.json
(written by main.py) through `triage` and has an LLM judge check assertions,
global ones plus one per voicemail. Judge and triage are both LLMs, so single
runs are flaky; each item runs three times and must pass twice.
"""

import json

import opik

from main import OUT_DIR, triage

SUITE_NAME = "whisper-vet-voicemail-triage-suite"
PROJECT = "whisper-vet-voicemail-triage"

GLOBAL_ASSERTIONS = [
    "The output names the caller and a callback phone number, and both "
    "appear in the transcript.",
    "The reason only restates symptoms or requests the caller actually "
    "mentioned. It adds no diagnosis, medical advice or invented facts.",
]

ITEM_ASSERTIONS = {
    "biscuit-chocolate": "Urgency is emergency: the dog ate chocolate and is shaking.",
    "pepper-limp": "Urgency is urgent: a limping cat that is still eating and alert.",
    "juniper-refill": "Urgency is routine: a medication refill with no symptoms.",
    "clover-not-eating": "Urgency is emergency: a rabbit that stopped eating and passing droppings, despite the polite tone.",
    "milo-vaccines": "Urgency is routine: a vaccine and neutering booking.",
}


def task(item: dict) -> dict:
    # Returning input + output is what the judge reads for each assertion.
    result = triage(item["transcript"])
    return {"input": {"transcript": item["transcript"]}, "output": result}


if __name__ == "__main__":
    path = OUT_DIR / "transcripts.json"
    if not path.exists():
        raise SystemExit("No transcripts yet: run `uv run main.py` first.")
    records = json.loads(path.read_text())

    client = opik.Opik()
    # A test suite bundles items with LLM-judge assertions. project_name keeps
    # the suite and its experiments in this example's project.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT,
        global_assertions=GLOBAL_ASSERTIONS,
        # Execution policy: run every item 3 times, pass if 2 runs pass. This
        # absorbs judge noise without hiding a real regression.
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )

    existing = {item["data"]["voicemail"] for item in suite.get_items()}
    for r in records:
        if r["id"] not in existing:
            suite.insert(
                [
                    {
                        "data": {"voicemail": r["id"], "transcript": r["transcript"]},
                        "assertions": [ITEM_ASSERTIONS[r["id"]]],
                    }
                ]
            )

    # run_tests creates one experiment in Opik, with a verdict per assertion.
    result = opik.run_tests(test_suite=suite, task=task)
    print(f"\nPass rate: {result.pass_rate:.0%}")
    opik.flush_tracker()
