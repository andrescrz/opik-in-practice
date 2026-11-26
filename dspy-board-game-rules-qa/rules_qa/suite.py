import dspy
import opik

from .config import MODEL, PROJECT_NAME
from .data import TEST
from .program import answer

SUITE_NAME = "lanternfall-rules-qa"

# Judged by an LLM for every item, on top of each item's own assertion.
GLOBAL_ASSERTIONS = [
    "The answer ends with a section citation of the exact form '[§<number>.<number>]', "
    "such as [§2.2], citing exactly one rulebook section",
    "The section cited in the answer is the rulebook section that actually "
    "contains the answer",
    "Apart from the citation, the answer is one short phrase or sentence that "
    "directly gives the requested rule, with no extra explanation",
]


def build_suite(client: opik.Opik):
    # A test suite is a dataset plus LLM-judged assertions. Scoping it to the
    # project makes the experiments appear in this project, not "Default Project".
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    # insert() skips items that already exist, so re-runs don't duplicate.
    suite.insert([
        {"data": {"question": question, "section": section},
         "assertions": [assertion]}
        for question, section, assertion in TEST
    ])
    return suite


def run_suite(suite, program: dspy.Module, experiment_name: str, compiled: bool):
    def task(item: dict) -> dict:
        return {"input": {"question": item["question"]},
                "output": answer(program, item["question"])}

    # run_tests runs the task on every item, has a judge model check each
    # assertion, and records one experiment per call. Running it for the raw
    # and the compiled program against the same suite makes the two
    # experiments directly comparable in the Opik UI.
    return opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=experiment_name,
        experiment_config={"program": "ChainOfThought(RulesQuestion)",
                           "compiled": compiled, "model": MODEL},
        worker_threads=4,
        generate_report=False,
    )


def run_suite_comparison() -> None:
    from .compile import compile_program
    from .program import build_program

    suite = build_suite(opik.Opik())

    print("Running the suite against the uncompiled program...")
    before = run_suite(suite, build_program(), "uncompiled", compiled=False)

    print("\nCompiling with BootstrapFewShot...")
    compiled_program = compile_program()

    print("\nRunning the same suite against the compiled program...")
    after = run_suite(suite, compiled_program, "compiled", compiled=True)

    print("\n=== Same suite, before and after compiling ===")
    for label, result in [("uncompiled", before), ("compiled  ", after)]:
        print(f"{label}: {result.pass_rate:.0%} pass rate "
              f"({result.items_passed}/{result.items_total} items passed)")
    if after.experiment_url:
        print(f"\nView the runs: {after.experiment_url}")
