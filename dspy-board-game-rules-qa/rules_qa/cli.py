import argparse

from .config import load_env
from .program import answer, build_program, setup_dspy


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(prog="rules-qa", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    ask.add_argument("--compiled", action="store_true",
                     help="use the program saved by `rules-qa compile`")
    sub.add_parser("compile", help="compile with BootstrapFewShot and save it")
    args = parser.parse_args()

    setup_dspy()
    if args.command == "compile":
        from .compile import compile_program

        compile_program()
        print("Compiled program saved.")
        return

    program = build_program()
    if args.compiled:
        from .config import COMPILED_PATH

        program.load(COMPILED_PATH)
    print(answer(program, args.question))


if __name__ == "__main__":
    main()
