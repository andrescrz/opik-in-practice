import collections

import opik

from . import config, engine

# One item per syllabus section a student actually asks about. Each asserts the exact facts
# the answer must contain, so a pass means "right course, right number", not just "fluent".
ITEMS = [
    {"section": "grading", "question": "In CS 210, how much of the grade is the final exam, and what must I score on it to pass?",
     "assertions": ["The answer states the CS 210 final exam is worth 20% of the grade",
                    "The answer states a student must earn at least 50% on the final exam to pass"]},
    {"section": "grading", "question": "Does HIST 301 have a final exam, and what is the research paper worth?",
     "assertions": ["The answer states HIST 301 has no final exam",
                    "The answer states the research paper is worth 30% of the grade"]},
    {"section": "grading", "question": "What happens to my BIO 150 grade if I skip a field trip without a medical note?",
     "assertions": ["The answer states the final grade drops by one third of a letter grade (for example B to B-minus)"]},
    {"section": "late work", "question": "How late can I hand in a BIO 150 field notebook and still get partial credit?",
     "assertions": ["The answer states the notebook is accepted until the following Monday at noon with a 20% deduction"]},
    {"section": "late work", "question": "How many extension tokens do I get in CS 210 and how long is each one?",
     "assertions": ["The answer states students get two extension tokens per term",
                    "The answer states each token gives a 48-hour extension"]},
    {"section": "late work", "question": "Can I submit a HIST 301 reading response late?",
     "assertions": ["The answer states HIST 301 reading responses are not accepted late and score zero if missed"]},
    {"section": "office hours", "question": "When and where are Dr. Nandakumar's office hours?",
     "assertions": ["The answer states in-person hours are Mondays 1:00 to 3:00 PM in Aldridge Hall room 12",
                    "The answer mentions the virtual drop-in hour on Thursdays at 8:00 PM"]},
    {"section": "office hours", "question": "Where can I get help with CS 210 labs on a Monday evening?",
     "assertions": ["The answer states teaching assistants run a help room Mondays 5:00 to 7:00 PM in the Hollis Hall basement lab"]},
    {"section": "prerequisites", "question": "What do I need to have completed before taking CS 210?",
     "assertions": ["The answer states CS 110 with a grade of C or better is required",
                    "The answer states MATH 120 is required"]},
    {"section": "prerequisites", "question": "Do I need any prerequisites for BIO 150?",
     "assertions": ["The answer states BIO 150 has no formal prerequisites"]},
    {"section": "not covered", "question": "Are calculators allowed on the CS 210 midterm?",
     "assertions": ["The answer says the syllabus excerpts do not cover calculator use, rather than stating a rule"]},
]

GLOBAL_ASSERTIONS = [
    "Every number, time, room and course code in the answer appears in the retrieved excerpts; the answer invents no policy",
    "The answer is about the course the question names",
]

# Judge flakiness: run each item 3 times and require 2 passes.
EXECUTION_POLICY = {"runs_per_item": 3, "pass_threshold": 2}


def build_suite(client: opik.Opik):
    # A test suite is a dataset whose items carry assertions; project_name keeps it (and its
    # experiments) in this example's project instead of "Default Project".
    suite = client.get_or_create_test_suite(
        name=config.PROJECT_NAME,
        project_name=config.PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy=EXECUTION_POLICY,
    )
    # Items are deduplicated by content, so re-running does not pile up copies.
    suite.insert([
        {"data": {"question": i["question"], "section": i["section"]}, "assertions": i["assertions"]}
        for i in ITEMS
    ])
    return suite


def run_suite(query_engine):
    client = opik.Opik()
    suite = build_suite(client)

    def task(item: dict) -> dict:
        result = engine.ask(query_engine, item["question"])
        # The judge sees retrieved excerpts next to the answer, so it can check the
        # "invents no policy" assertion against what retrieval really returned.
        return {"input": item, "output": {
            "answer": result["answer"],
            "retrieved_excerpts": [s["text"] for s in result["sources"]],
        }}

    # run_tests sends each item through the task, has an LLM judge check every assertion, and
    # records an experiment with a pass/fail per item. No model override: the default judge works.
    return opik.run_tests(test_suite=suite, task=task, worker_threads=3, generate_report=False)


def summarize(result) -> dict[str, list[bool]]:
    by_section: dict[str, list[bool]] = collections.defaultdict(list)
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items passed)")
    for item_result in result.item_results.values():
        case = item_result.test_results[0].test_case.task_output["input"]
        by_section[case["section"]].append(item_result.passed)
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] ({case['section']}) {case['question']}")
        if not item_result.passed:
            for run in item_result.test_results:
                for score in run.score_results:
                    if score.scoring_failed or score.value != 1:
                        print(f"         failed: {score.name}: {score.reason}")
    print("\nBy section:")
    for section, passes in by_section.items():
        print(f"  {section}: {sum(passes)}/{len(passes)}")
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")
    return by_section
