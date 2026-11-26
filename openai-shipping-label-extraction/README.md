<div align="center">

# Read the Label, Then Check the Pixels

**`openai-shipping-label-extraction`**

*A vision model says the postcode is `SE15 4TR`. The trace shows you the label it was looking at.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Model](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat&logo=openai&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

</div>

---

Parcel labels get photographed sideways, smeared by rain, and corrected with a
biro. When a vision model reads one into structured fields and gets a postcode
wrong, the text of the output tells you nothing about *why*. Was the label
unreadable, or did the model misread clean print? This example reads nine
fictional shipping labels with `gpt-4o-mini` into a typed pydantic model, keeps
every label image attached to the trace that processed it, and checks the
results with an Opik test suite that is designed not to score 100%.

## What you'll build

- `labels.py` draws nine labels for three made-up carriers (Northwind Parcel,
  Kestrel Post, SwiftArrow Express) with Pillow. Three are clean. The others are
  rotated 90 degrees, tilted on a dark background, smeared across the tracking
  number, struck-through with a handwritten weight correction, struck-through
  with a handwritten postcode correction, and shrunk to a blurry thumbnail. The
  PNGs are committed (all under 40 KB) so the run never depends on drawing.
- `extract.py` sends one image to `gpt-4o-mini` and parses the reply straight
  into `LabelFields`: tracking number, carrier, service level, weight in kg,
  recipient name and postcode.
- `main.py` builds an Opik test suite from the labels. Each label carries three
  plain-language assertions holding the true values, three global assertions
  apply to every label, and an execution policy runs each label three times and
  needs two passes.
- `scoring.py` is a plain-Python field comparison, so you get a second opinion
  that doesn't depend on an LLM judge.

## See it in Opik

Open the **`openai-shipping-label-extraction`** project and go to **Traces**.
A full run leaves 27 traces (9 labels x 3 runs), each named `evaluation_task`.
Expand one: inside it are the `extraction_task` and `extract_label` spans, a
`chat_completion_parse` span of type *llm* with `gpt-4o-mini-2024-07-18`, token
counts and an estimated cost (about $0.0007 per extraction), and the judge's own
spans. Switch to the trace's **Attachments** tab and the label PNG is there,
rendered in place, next to the fields the model returned. All 27 traces carry
their image; there are three per label file.

That pairing is the debugging story. Open a trace for
`label_08_handwritten_postcode.png`: the printed postcode `SE15 4TR` is struck
through and `SE15 4TY` is written beneath it in blue, but the model returned
`SE15 4TR`. It read the print and ignored the correction, despite a system prompt
that says handwritten values win. You can see that in two seconds because the
image sits beside the output.

Then open **Test suites -> openai-shipping-label-extraction** and the experiment
**`labels-gpt-4o-mini`**. In the run committed to this write-up, 7 of 9 labels
passed. The two failures are the ones you would hope a suite finds:

- `label_06_smudged_tracking.png`: the tracking number is a grey smear and the
  model returned an empty string in every run, so the "tracking number is
  SA-440823-9015" assertion fails 3/3. Returning nothing is the honest answer
  here, but it is still a miss, and the suite says so.
- `label_08_handwritten_postcode.png`: the corrected postcode is missed, as above.

`label_07_handwritten_weight.png` passes: the model read the handwritten `3.1`
rather than the struck-through `2.4` in all three runs. An earlier run of the same
code had one run garble that label's tracking number (`NW66209448113`) and the
item still passed, because the policy is two out of three; the console line
`wrong fields: [...]` printed next to a `PASS` is how you spot a flaw the policy
absorbed. Judge-based pass rates move a little between runs, so yours may differ.

The script ends with a per-field exact-match table over all 27 runs: tracking
number 89% (the three smudged runs), postcode 89% (the three uncorrected runs), and 100% for carrier, service level, weight and
recipient. Carrier and name come back upper-cased from the label's printed
headers, and the scorer ignores case.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start Opik (`./opik.sh` from the Opik repo, or use Opik Cloud).
2. `cp .env.example .env`, then fill in `OPENAI_API_KEY`. For Opik Cloud also set `OPIK_API_KEY`, `OPIK_WORKSPACE` and `OPIK_URL_OVERRIDE`; for a local Opik the defaults in the file work. (A `.env` in any parent folder is found too.)
3. `uv sync`
4. `uv run python main.py` (about a minute and a few cents; add `uv run python labels.py` first only if you want to redraw the images).
5. Open the project in Opik as described above; the experiment link is printed at the end.

Offline tests, no keys and no Opik needed:

```bash
OPIK_TRACK_DISABLE=true uv run pytest
```

## Poke around

- Change `"detail": "high"` to `"low"` in `extract.py` and re-run. Watch the prompt tokens per span fall and see which labels stop passing first.
- Make the smudge in `labels.py` lighter (a blur radius of 4 instead of 9) and find the point where the model starts reading the tracking number again, or starts inventing one.
- Add a tenth label with two corrections on the same label. Suites deduplicate identical items, so a re-run only adds the new one.
- Set the suite policy to `runs_per_item: 1`, run it three times, and compare the pass rate drift with the 2-of-3 policy.

## Gotchas we hit

- **Every call prints `UserWarning: Pydantic serializer warnings ... field_name='parsed'`.**
  `track_openai` also wraps `client.chat.completions.parse`, and logging the
  parsed response makes pydantic complain that `parsed` is not `None`. The span
  output is logged correctly; only the noise is wrong. Silence it in `extract.py`:
  `warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)`.
- **`attachment_list` returns nothing when you look at traces named `extract_label`.**
  Inside `run_tests` the root trace is `evaluation_task`; `extract_label` is a
  span in it, and `update_current_trace(attachments=...)` puts the image on the
  root trace. Query attachments with `entity_type="trace"` and the id of the
  `evaluation_task` trace, with `path=base64(<your Opik API url>)`.

## How it's put together

- `labels.py`: label specs (the ground truth) plus the Pillow drawing and damage; `python labels.py` regenerates `data/`.
- `extract.py`: the `LabelFields` model, the prompt, and the traced `extract_label`, which attaches the image to its trace.
- `main.py`: the test suite, its assertions and execution policy, and the console summary.
- `scoring.py`: deterministic per-field matching and accuracy.
- `tests/`: stubbed-model tests for scoring, the label fixtures and assertions, and `extract_label` called with tracking disabled.
- `data/`: the nine label PNGs.
- `.env.example`, `pyproject.toml`: configuration and dependencies.

---

*built with Opik · inspired by Opik's examples and documentation*
