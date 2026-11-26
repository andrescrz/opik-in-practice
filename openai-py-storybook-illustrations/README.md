# openai-py-storybook-illustrations

*A fictional picture book, four AI illustrations, and a trace that carries each picture with the brief that made it.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/openai-Images%20API-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3-2f54eb?style=flat)

You can't `grep` a picture. Once an art director starts tweaking the wording of an illustration brief, the PNGs pile up in a folder and nobody can say which wording produced the hedgehog that made it into the book. This example generates illustrations for *The Lantern Hedgehog*, a picture book that doesn't exist, and makes two things visible in Opik: each generated PNG is an attachment on its trace, and the brief is a prompt-library entry with two versions you can diff.

## What you'll build

A small Python app. `data/scenes.json` holds two scene descriptions (page 3, page 7). A single brief template turns each scene into an image prompt, and the OpenAI Images API draws it. The brief exists in two versions:

- **v1**: page, setting, action, mood. The first draft anyone writes.
- **v2**: the same plus art-direction rules: soft watercolor, a fixed look for Pip (cream face, red knitted scarf), no lettering, a calm lower third for the story text.

Both versions are rendered for both scenes: four images, one trace each. The brief lives in the Opik prompt library; the code creates it once and never again, so the library holds exactly two versions however many times you run the app.

## See it in Opik

Open the **openai-py-storybook-illustrations** project. The Traces tab lists four `illustrate-page` traces, tagged `v1` or `v2` plus the scene id (`lantern-hill`, `river-crossing`). Open one and look at the Attachments tab: the PNG itself (roughly 1.6-2 MB) is there, e.g. `v2-lantern-hill.png`. The input shows the fully rendered prompt; the metadata names the prompt version and links to the prompt-library entry.

Expand the trace and there is one child `images.generate` span of type `llm`, showing model `gpt-image-1-mini`, provider `openai` and the usage the Images API reported (66 prompt and 272 completion tokens for the v1 lantern page, 146 and 272 for v2). Opik priced these: `total_estimated_cost` was about $0.00013 for v1 spans and $0.00029 for v2 spans, so the longer v2 brief is visibly more expensive, in prompt tokens at least.

Then open **Prompts** and `storybook-illustration-brief`: two versions, and the diff view shows v2 adding the four style rules. Put the v1 and v2 attachments side by side. In our run the v2 Pip wore the red scarf and the paint looked like watercolor on paper; the v1 Pip was scarf-less on a darker, oil-painting-like sky. Image models treat briefs as suggestions, so your pictures will differ, but the trace tells you which version asked for what.

## Run it yourself

1. `cp .env.example .env` (or reuse a repo-root `.env`) and set `OPENAI_API_KEY`. Point `OPIK_URL_OVERRIDE` at your Opik; for Opik Cloud set `OPIK_API_KEY` and `OPIK_WORKSPACE` instead.
2. `uv run main.py`
3. Open the project above in Opik. The PNGs are also written to `output/` (git-ignored, regenerated each run).
4. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest`

A run takes about 40 seconds and costs well under a cent: four images, quality `low`, 1024x1024.

## Poke around

- Re-run `uv run main.py` a few times. The library still shows two versions, and each run adds four traces.
- Edit `BRIEF_V2` in `storybook/briefs.py`, then delete the prompt in the Opik UI and re-run to register your new wording as the new v2.
- Add a third scene to `data/scenes.json` (keep keys `id`, `page`, `setting`, `action`, `mood`) and compare how consistently Pip looks across v1 and v2.
- Set `IMAGE_MODEL=gpt-image-1.5` and compare the cost on the `images.generate` span.

## Gotchas we hit

**`The model 'gpt-image-1' does not exist`** (a 400 `image_generation_user_error`). The model isn't served to every account any more. List what your key can see (`client.models.list()`) and set one, as this example does with `IMAGE_MODEL=gpt-image-1-mini` as its default.

**The image call isn't in the trace at all.** `track_openai` instruments chat, completions, embeddings and responses, not `images.generate`. Decorate your own function instead and report the model, provider and usage by hand:

```python
@opik.track(type="llm")
def generate_png(...):
    opik.opik_context.update_current_span(model=MODEL, provider="openai", usage={...})
```

With model and provider set, Opik computed a cost for `gpt-image-1-mini`.

**`PromptPlaceholdersDontMatchFormatArguments`.** `Prompt.format(**kwargs)` requires exactly the template's placeholders; our scene dicts carry an extra `id`, which raises. Pass only the fields the template uses.

**A new prompt version appears on every run.** `create_prompt` compares against the *latest* version, so naively creating v1 then v2 each run would flip-flop. `storybook/library.py` only creates what's missing (checked via `get_prompt_history`), which keeps it at two versions.

## How it's put together

- `main.py`: loads `.env`, sets the Opik project, ensures the prompt versions, generates the four images, flushes.
- `storybook/briefs.py`: the v1 and v2 brief templates, the scene loader, and a small renderer.
- `storybook/library.py`: idempotent prompt creation and the v1 to v2 diff.
- `storybook/illustrate.py`: the traced image call and the per-page trace with its attachment.
- `data/scenes.json`: the two scene descriptions.
- `tests/test_storybook.py`: offline tests (rendering, idempotent versions against a fake library, a traced call with tracking disabled).

---

*built with Opik · inspired by Opik's examples and documentation*
