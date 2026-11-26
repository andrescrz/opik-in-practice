import argparse

import opik

from .program import answer, build_program, setup_dspy


def main() -> None:
    parser = argparse.ArgumentParser(prog="rules-qa", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    ask.add_argument("--compiled", action="store_true",
                     help="use the program saved by `rules-qa compile`")
    sub.add_parser("compile", help="compile with BootstrapFewShot and save it")
    sub.add_parser("run", help="run the suite on the raw and the compiled program")
    args = parser.parse_args()

    setup_dspy()
    if args.command == "compile":
        from .compile import compile_program

        compile_program()
        print("Compiled program saved.")
        opik.flush_tracker()
        return

    if args.command == "run":
        from .suite import run_suite_comparison

        run_suite_comparison()
        opik.flush_tracker()
        return

    program = build_program()
    if args.compiled:
        from .config import COMPILED_PATH

        program.load(COMPILED_PATH)
    print(answer(program, args.question))
    # Traces are sent from a background thread; flush so a short-lived CLI
    # run doesn't exit before they are delivered.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
