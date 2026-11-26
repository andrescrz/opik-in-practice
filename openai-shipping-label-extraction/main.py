"""Extract fields from every label image in data/ and print them next to the truth."""

from extract import extract_label
from labels import LABELS


def main() -> None:
    for label in LABELS:
        fields = extract_label(f"data/{label['file']}")
        print(f"{label['file']}  ({label['damage']})")
        print(f"  got      {fields.model_dump()}")
        print(f"  expected {label['expected']}\n")


if __name__ == "__main__":
    main()
