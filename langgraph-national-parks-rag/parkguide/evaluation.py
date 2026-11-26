import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import ContextPrecision, Hallucination

DATASET_NAME = "national-parks-visitor-questions"

DATASET_ITEMS = [
    {"question": "How much does a backcountry permit cost and how far ahead can I book?",
     "expected_output": "9 dollars per person per night; reservations open 60 days before the trip."},
    {"question": "Are dogs allowed on Ember Ridge?",
     "expected_output": "No, dogs are not allowed on Ember Ridge because of ground-nesting birds."},
    {"question": "Which trail can I take with a stroller?",
     "expected_output": "The Mossglass Lake Walk, a flat 3 km boardwalk, is stroller and wheelchair accessible."},
    {"question": "What time is check-out at Fernwater and when are quiet hours?",
     "expected_output": "Check-out is by 11 am; quiet hours run from 10 pm to 6 am."},
    {"question": "How close can I get to a bear?",
     "expected_output": "Keep at least 100 metres from a bear."},
    {"question": "Does the annual pass cover camping?",
     "expected_output": "No, the Hollow Annual Pass covers day-use entry only, not campground fees or backcountry permits."},
    # Paraphrase with no word in common with the guide's "dogs" section: BM25 can't bridge it.
    {"question": "Can I take my pooch on the hike up to the fire lookout?",
     "expected_output": "No, dogs are not allowed on Ember Ridge, the trail to the fire lookout."},
    # Not in the guide at all: the right answer is "I don't know".
    {"question": "Does the park rent kayaks on Mossglass Lake?",
     "expected_output": "The guide does not say; the assistant should say it doesn't know."},
]


def run_experiment(app, k: int, project_name: str):
    """Score `app` (a graph that answers a question) over the dataset and return the result."""
    client = opik.Opik()
    # Datasets are project-scoped: passing project_name keeps the dataset and its experiments
    # in this example's project rather than "Default Project". insert() skips duplicates on re-runs.
    dataset = client.get_or_create_dataset(name=DATASET_NAME, project_name=project_name)
    dataset.insert(DATASET_ITEMS)

    def task(item: dict) -> dict:
        result = app.invoke({"question": item["question"]})
        return {"output": result["answer"], "context": result["context"]}

    # Hallucination judges the answer against the retrieved context (1 = made things up);
    # ContextPrecision judges whether that context was the right material for the question
    # (1 = precise). Together they separate "bad search" from "bad answer". Both use an LLM judge.
    return evaluate(
        dataset=dataset,
        task=task,
        scoring_metrics=[Hallucination(), ContextPrecision()],
        # The metrics expect `input`; the dataset column is called `question`.
        scoring_key_mapping={"input": "question"},
        experiment_name=f"top-{k}-sections",
        # Stored on the experiment so runs can be told apart in the comparison view.
        experiment_config={"k": k, "model": "gpt-4o-mini", "retriever": "bm25"},
        task_threads=4,
    )


def mean_scores(evaluation) -> dict[str, float]:
    aggregated = evaluation.aggregate_evaluation_scores().aggregated_scores
    return {name: stats.mean for name, stats in aggregated.items()}
