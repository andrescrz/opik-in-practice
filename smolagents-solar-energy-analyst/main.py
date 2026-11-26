"""A smolagents CodeAgent that answers questions about a solar farm's CSV."""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=False))  # walks up from this file to the first .env

from tracing import PROJECT_NAME, setup_tracing  # noqa: E402

from smolagents import CodeAgent, OpenAIServerModel  # noqa: E402

CSV_PATH = Path(__file__).parent / "data" / "solar_farm.csv"

BRIEFING = f"""\
You are the performance analyst for Meadowbrook Solar, a four-array solar farm.
Daily production data for 2025-04-01 to 2025-06-30 is the CSV at: {CSV_PATH}

Columns: date (YYYY-MM-DD), array_id (A-D), kwh (energy produced that day),
irradiance_kwh_m2 (sunshine that day, same for all arrays), inverter_faults
(fault events logged that day).

Load it with pandas and answer with concrete numbers from the data. A healthy
array's kwh tracks irradiance, so compare output to irradiance, not just to
other days. Answer in two or three plain sentences.
"""

QUESTIONS = [
    "Which array has been underperforming relative to the sunshine it receives, "
    "and from roughly what date? Report each array's average kwh per unit of "
    "irradiance before and after 2025-05-14, and the date the drop starts.",
    "One array had a burst of inverter faults on several consecutive days, "
    "against a background of occasional single faults on every array. Which "
    "array, which dates, how many faults in the burst, and what was its "
    "average kwh on those days?",
    "Was there any day when every array produced about zero despite good "
    "sunshine? Give the date and the irradiance that day.",
]


def build_agent() -> CodeAgent:
    # The model writes Python; the local executor may only import pandas on top
    # of smolagents' safe defaults.
    return CodeAgent(
        tools=[],
        model=OpenAIServerModel(model_id="gpt-4o-mini"),
        additional_authorized_imports=["pandas"],
        max_steps=6,
    )


def main() -> None:
    provider = setup_tracing()
    agent = build_agent()
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'=' * 72}\nQuestion {i}: {question}\n{'=' * 72}")
        answer = agent.run(BRIEFING + "\nQuestion: " + question)
        print(f"\nAnswer {i}: {answer}")

    # Flush and stop the exporter so the last spans reach Opik before the process exits.
    provider.shutdown()
    print(f"\nDone. Open the '{PROJECT_NAME}' project in Opik: one trace per question.")


if __name__ == "__main__":
    main()
