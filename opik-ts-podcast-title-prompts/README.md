# opik-ts-podcast-title-prompts

*A podcast-title prompt that lives in Opik's prompt library, gets edited once, and is graded before and after: 0 of 6 episodes pass with v1, 6 of 6 with v2.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![opik](https://img.shields.io/badge/opik-2.3.5-2f54eb?style=flat)
![openai](https://img.shields.io/badge/openai-6.x-412991?style=flat)

Nobody notices a prompt edit until the output changes. The fictional **Foxglove Audio** network asks a model to title episodes from a couple of lines of notes. The first prompt ("write a catchy, exciting title") returns things like *"Melting Mysteries: Middle Schoolers Unravel the Science of Snowbanks!"*, which breaks every house rule the editors have. This example shows how to fix that in a way you can audit: the prompt is stored in Opik, each edit is an immutable version, you can diff versions, and the same test suite is run against each one.

## What you'll build

- `src/main.ts` registers the prompt `episode-title-writer` in the prompt library twice (v1 generic, v2 with explicit rules), prints the v1 to v2 diff, and runs one Opik **test suite** per version using `gpt-4o-mini` for both the title writer and the judge.
- The suite `episode-title-rules` holds six invented episodes. Four assertions apply to every episode (eight words or fewer, no colon, no hype words, no emoji/hashtags/quotes); episodes with a guest get a fifth: the title must contain the guest's full name. An episode passes only if all its assertions pass.
- The script is safe to re-run: it checks the existing version history first, so the prompt always ends with exactly two versions.

## See it in Opik

Open the project **opik-ts-podcast-title-prompts**.

- **Prompt library**: `episode-title-writer` has two versions, v1 and v2. Open the version list and compare them to see the diff: v1 is one sentence, v2 adds a five-line rule list. Each version carries a `change` note in its metadata.
- **Experiments**: two experiments, `episode-title-writer-v1` and `episode-title-writer-v2`, each linked to the prompt version it used. In my verified run v1 passed **0 of 6** items and v2 passed **6 of 6**. Open v1 and you will see failed assertions such as "The title does not contain a colon character (:)" next to titles like *"Crafting Tradition: Anneliese Brandt's Wooden Sailboat Revival"*; open v2 and titles read like *"Dev Pillai on Repairing Historic Church Organs"*.
- **Traces**: 12 traces named `evaluation_task` (6 per version). Each holds the `llm_task` span, a `write_title` span from `opik-openai` with model `gpt-4o-mini`, token usage and cost, and the judge's `llm_judge` / `model.generateText` spans (type `llm`, with usage and cost).

LLM judges are noisy. Across four full runs while building this, v1 scored 0% three times and 17% once, v2 scored 100% three times and 83% once, until I reworded the colon assertion to ask about the literal `:` character. After that, three consecutive runs and the final run all gave 0% / 100%. Expect small wobble on borderline titles.

## Run it yourself

1. Start Opik locally (or have an Opik Cloud key) and have an OpenAI key.
2. `cp .env.example .env` and fill in `OPENAI_API_KEY` (a `.env` further up the tree also works). Local Opik defaults to `http://localhost:5173/api/`.
3. `npm install`
4. `npm run demo` (about 20 seconds, roughly one cent of model calls)
5. Open the project in Opik as described above.

Tests need no keys and no server: `OPIK_TRACK_DISABLE=true npm test` (the SDK's switch that turns `track()` into a pass-through). `npm run typecheck` runs `tsc`.

## Poke around

- Edit the text of `V2` in `src/prompts.ts`, for example drop the eight-word rule, and rerun: the library gains a v3 and you can see which assertion starts failing.
- Add an episode to `src/episodes.ts` on a fresh suite (delete `episode-title-rules` in the UI first, items are only inserted when the suite is empty).
- Add an assertion to `GLOBAL_ASSERTIONS` such as "The title starts with a verb" and compare the two experiments again.
- Change `temperature` in `src/titles.ts` and see whether v1 can ever pass by luck.

## Gotchas we hit

- **`npm install` fails with `ERESOLVE ... peer opik@"^1.8.61" from opik-openai@2.3.5`.** The `opik-openai` package declares a peer range that excludes `opik` 2.x. Pin both and add `"overrides": { "opik-openai": { "opik": "$opik" } }` to `package.json`, as this example does.
- **The version's change description is empty in Opik.** `createPrompt({ changeDescription })` is accepted but the backend returned no `change_description` for the versions on this SDK/server pair. The note is stored as `metadata: { change: "..." }` instead.
- **Every OpenAI call shows up as its own trace, outside the experiment item.** `trackOpenAI(client)` opens a new trace per call by default. Inside a test-suite task, pass the running span: `trackOpenAI(openai, { client, parent: getTrackContext()?.span })`. The span it creates has type `general` (with model, usage and cost filled in).
- **The judge says a title with a colon has no colon.** A vague assertion ("no colon or dash splitting title and subtitle") was graded wrongly in some runs. State the check literally: `"The title does not contain a colon character (:)"`.

## How it's put together

- `src/main.ts`: loads `.env`, wires Opik and OpenAI, prints the diff, runs `runTests` per version, flushes.
- `src/library.ts`: idempotent prompt-version sync and test-suite creation.
- `src/prompts.ts`: the two prompt texts and the assertion strings.
- `src/episodes.ts`: the six fictional episodes.
- `src/titles.ts`: builds the model call and cleans the reply.
- `tests/titles.test.ts`: message building, cleaning, stubbed model call, assertion data.
- `tests/library.test.ts`: re-running never adds a third prompt version.
- `tests/tracked.test.ts`: a `track()`-wrapped call with tracking disabled.
- `package-lock.json`: pinned dependency tree.

---

*built with Opik · inspired by Opik's examples and documentation*
