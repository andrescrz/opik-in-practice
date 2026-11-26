"""Tune the review-intent prompt with Opik's MetaPromptOptimizer and keep the winner."""

import opik
from classify import BASELINE_SYSTEM, MODEL, PROJECT_NAME, classify, intent_match
from opik_optimizer import ChatPrompt, MetaPromptOptimizer
from reviews import REVIEWS

DATASET_NAME = "app-review-intents"
LIBRARY_PROMPT = "app-review-intent-classifier"
MAX_TRIALS = 8  # budget cap: candidate prompts the optimizer may score

def exact_label_match(dataset_item: dict, llm_output: str) -> float:
    """1.0 only if the reply is exactly the labeled intent, so extra words such as a rationale score 0."""
    return intent_match(dataset_item["label"], llm_output)


def main() -> None:
    client = opik.Opik(project_name=PROJECT_NAME)

    # Datasets are project-scoped: passing project_name keeps the dataset (and the
    # experiments the optimizer creates from it) out of "Default Project".
    dataset = client.get_or_create_dataset(
        name=DATASET_NAME,
        description="20 labeled Pebblepad app-store reviews (5 intents)",
        project_name=PROJECT_NAME,
    )
    # Opik deduplicates identical rows, so re-running does not grow the dataset.
    dataset.insert([{"review": text, "label": label} for text, label in REVIEWS])


    # {review} is filled from the dataset column of the same name on every trial.
    prompt = ChatPrompt(
        name=LIBRARY_PROMPT,
        system=BASELINE_SYSTEM,
        user="{review}",
        model=f"openai/{MODEL}",
    )

    # Prompt library v1 = the baseline, saved first so the library records the
    # before/after pair (the Prompts page shows both versions and a diff).
    client.create_chat_prompt(
        name=LIBRARY_PROMPT,
        messages=[
            {"role": "system", "content": BASELINE_SYSTEM},
            {"role": "user", "content": "{{review}}"},
        ],
        change_description="Baseline hand-written prompt (pre-optimization)",
        project_name=PROJECT_NAME,
    )

    optimizer = MetaPromptOptimizer(
        model=f"openai/{MODEL}",  # the model that analyses failures and proposes rewrites
        prompts_per_round=3,
        seed=7,
        verbose=1,
    )

    # project_name routes the Optimization run, one experiment per trial and the
    # LLM traces behind them into our project; each trial is a point on the score curve.
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=exact_label_match,
        n_samples=len(REVIEWS),
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,
    )

    initial = result.initial_score or 0.0
    best = result.score
    winner = result.prompt.get_messages()
    # The optimizer uses {review}; the prompt library uses mustache {{review}}.
    for message in winner:
        message["content"] = message["content"].replace("{review}", "{{review}}")

    # Library v2 = the winner. Only a real gain is saved; the version history stays an honest record.
    if best > initial:
        client.create_chat_prompt(
            name=LIBRARY_PROMPT,
            messages=winner,
            change_description=f"MetaPromptOptimizer winner: accuracy {initial:.3f} -> {best:.3f} on {DATASET_NAME}",
            project_name=PROJECT_NAME,
        )

    # Re-score the winner through the traced classifier: one classify_review trace
    # per review in the project, an independent check of the optimizer's number.
    check = sum(intent_match(label, classify(text, system=winner[0]["content"])) for text, label in REVIEWS)

    # get_run_link() opens in the UI's currently active project, so the run can
    # look empty. Build a link pinned to the project that holds the run instead.
    opt = client.rest_client.optimizations.get_optimization_by_id(result.optimization_id)
    ui_base = client.config.url_override.rstrip("/").removesuffix("/api")

    print("\n" + "=" * 64)
    print(f"baseline accuracy : {initial:.3f}")
    print(f"best accuracy     : {best:.3f}  ({best - initial:+.3f})")
    print(f"re-scored winner  : {check / len(REVIEWS):.3f}")
    print(f"trials completed  : {result.details.get('trials_completed')} (budget {MAX_TRIALS})")
    print(f"run link          : {ui_base}/{client.config.workspace}/projects/{opt.project_id}/optimizations/{result.optimization_id}")
    print("=" * 64)
    print("\nWinning system prompt:\n")
    print(winner[0]["content"])

    # Traces upload in the background; flush so a short script doesn't exit before they land.
    opik.flush_tracker()
    client.flush()


if __name__ == "__main__":
    main()
