import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

from langchain_openai import ChatOpenAI

from parkguide.corpus import load_sections
from parkguide.graph import build_graph
from parkguide.retriever import KeywordRetriever

DEMO_QUESTIONS = [
    "How much does a backcountry permit cost and how far ahead can I book?",
    "Are dogs allowed on Ember Ridge?",
    "Can I bring my own firewood to Cinder Flat?",
    "Is there a shuttle bus from the airport to the park?",
]


def main() -> None:
    retriever = KeywordRetriever(load_sections())
    app = build_graph(retriever, ChatOpenAI(model="gpt-4o-mini", temperature=0))
    for question in DEMO_QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")


if __name__ == "__main__":
    main()
