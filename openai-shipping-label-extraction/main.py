"""Run the shipping-label test suite: extract every label, judge the output in Opik."""

import opik

from extract import MODEL, PROJECT_NAME, extract_label
from labels import LABELS
from scoring import accuracy, field_matches

# Rules every extraction must satisfy, judged from the output alone.
GLOBAL_ASSERTIONS = [
    "The output has all six fields (tracking_number, carrier, service_level, weight_kg, "
    "ship_to_name, ship_to_postcode) and weight_kg is a number",
    "ship_to_postcode contains only the postcode itself, with no label words like 'SHIP TO' "
    "and no city or street",
    "Values come from the label; none is a placeholder such as 'unknown', 'N/A' or 'example'",
]


def assertions_for(label: dict) -> list[str]:
    # The expected values live only in the assertions, so the judge compares the output
    # to the truth instead of reading the answer out of the item's input.
    e = label["expected"]
    return [
        f"The carrier is {e['carrier']}, the service level is {e['service_level']} and the "
        f"recipient is {e['ship_to_name']} (letter case does not matter)",
        f"The tracking number is {e['tracking_number']} (spacing and dashes as printed)",
        f"The weight is {e['weight_kg']} kg and the postcode is {e['ship_to_postcode']} ({label['note']})",
    ]


TEST_ITEMS = [
    {
        "data": {"image": f"data/{label['file']}", "damage": label["damage"]},
        "assertions": assertions_for(label),
    }
    for label in LABELS
]


def main() -> None:
    client = opik.Opik()
    # A test suite stores the items and their assertions. runs_per_item=3 / pass_threshold=2
    # makes an item pass when 2 of 3 runs pass, so one flaky model read or judge call
    # doesn't flip the verdict. Created with project_name so the run lands in this project.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    suite.insert(TEST_ITEMS)

    def extraction_task(item: dict) -> dict:
        return {"input": item, "output": extract_label(item["image"]).model_dump()}

    # run_tests creates an experiment: per item it runs the task, then an LLM judge
    # grades each assertion. Each extraction is still its own trace with the image attached.
    result = opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name=f"labels-{MODEL}",
        worker_threads=3,
        generate_report=False,
    )

    expected_by_image = {f"data/{label['file']}": label["expected"] for label in LABELS}
    print(f"\nJudge pass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} labels)")
    all_matches = []
    for item_result in result.item_results.values():
        outputs = [r.test_case.task_output for r in item_result.test_results]
        image = outputs[0]["input"]["image"]
        matches = [field_matches(o["output"], expected_by_image[image]) for o in outputs]
        all_matches += matches
        wrong = sorted({name for m in matches for name, ok in m.items() if not ok})
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {image}" + (f"  wrong fields: {wrong}" if wrong else ""))
    print("Exact-match accuracy per field, over all runs:")
    for name, value in accuracy(all_matches).items():
        print(f"  {name:<17} {value:.0%}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Flush so queued traces, attachments and experiment items are sent before the process exits.
    opik.flush_tracker()
    client.flush()


if __name__ == "__main__":
    main()
