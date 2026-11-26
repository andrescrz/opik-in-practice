import type { Opik, Prompt } from "opik";
import { GLOBAL_ASSERTIONS, PROMPT_NAME, V1, V2, guestAssertion } from "./prompts.js";
import { EPISODES } from "./episodes.js";

// createPrompt only skips a duplicate when the text matches the *latest*
// version. Re-registering v1 after v2 exists would append a third version
// holding v1's text, so we check the whole history first.
export async function syncPromptVersions(client: Opik): Promise<{ v1: Prompt; v2: Prompt }> {
  const existing = await client.getPrompt({ name: PROMPT_NAME });
  const known = new Set(existing ? (await existing.getVersions()).map((v) => v.prompt) : []);

  for (const spec of [V1, V2]) {
    if (known.has(spec.text)) continue;
    // Each new text becomes a new immutable version in the prompt library.
    // The changeDescription option is not persisted by the backend on this
    // SDK/server pair, so the note travels as version metadata instead.
    await client.createPrompt({
      name: PROMPT_NAME,
      prompt: spec.text,
      metadata: { change: spec.changeDescription },
    });
  }

  // Fetching by version number pins exactly which wording each run uses.
  const v1 = await client.getPrompt({ name: PROMPT_NAME, version: "v1" });
  const v2 = await client.getPrompt({ name: PROMPT_NAME, version: "v2" });
  if (!v1 || !v2) throw new Error("Prompt versions v1/v2 not found after sync");
  return { v1, v2 };
}

export async function syncSuite(client: Opik, projectName: string) {
  // A test suite is a dataset plus plain-language assertions that an LLM judge
  // checks on every output. Scoped to the project so its runs land there.
  const suite = await client.getOrCreateTestSuite({
    name: "episode-title-rules",
    description: "Episode notes with the rules a good title must follow",
    globalAssertions: GLOBAL_ASSERTIONS,
    projectName,
  });
  if (!(await suite.getItemsCount())) {
    await suite.insert(
      EPISODES.map((ep) => ({
        data: { show: ep.show, notes: ep.notes, guest: ep.guest ?? null },
        assertions: ep.guest ? [guestAssertion(ep.guest)] : [],
      })),
    );
  }
  return suite;
}
