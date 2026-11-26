import argparse

from . import config, engine, index, pdfgen, questions


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="syllabus_qa", description="Q&A over generated course syllabi")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate", help="(re)write the syllabus PDFs into data/syllabi")
    ask_p = sub.add_parser("ask", help="answer one question")
    ask_p.add_argument("question")
    sub.add_parser("demo", help="answer the four demo questions")
    args = parser.parse_args(argv)

    if args.command == "generate":
        for path in pdfgen.generate_all(config.DATA_DIR):
            print(f"wrote {path}")
        return

    query_engine = engine.make_engine(index.build_index())
    asked = [args.question] if args.command == "ask" else questions.DEMO_QUESTIONS
    for question in asked:
        result = engine.ask(query_engine, question)
        print(f"Q: {question}\nA: {result['answer']}")
        print("   from: " + ", ".join(sorted({s["file"] for s in result["sources"]})) + "\n")
