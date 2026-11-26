"""Score the baseline prompt on the labeled reviews."""

from classify import classify, intent_match
from reviews import REVIEWS


def main() -> None:
    hits = 0.0
    for text, label in REVIEWS:
        answer = classify(text)
        score = intent_match(label, answer)
        hits += score
        print(f"[{'ok' if score else 'x '}] want={label:<20} got={answer[:60]!r}")
    print(f"\nbaseline accuracy: {hits / len(REVIEWS):.3f}")


if __name__ == "__main__":
    main()
