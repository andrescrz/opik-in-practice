import { config } from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// Load the nearest .env (walking up from this folder) before any Opik client
// exists, so OPIK_URL_OVERRIDE / OPIK_WORKSPACE are set when it reads its config.
function loadEnv() {
  let dir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  for (;;) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) return void config({ path: candidate });
    const parent = dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
loadEnv();

const { Opik, runTests, getTrackContext } = await import("opik");
const { trackOpenAI } = await import("opik-openai");
const { default: OpenAI } = await import("openai");
const { syncPromptVersions, syncSuite } = await import("./library.js");
const { writeTitle, MODEL } = await import("./titles.js");
const { PROMPT_NAME } = await import("./prompts.js");
type EpisodeData = import("./episodes.js").Episode;

const PROJECT = process.env.OPIK_PROJECT_NAME ?? "opik-ts-podcast-title-prompts";
process.env.OPIK_PROJECT_NAME = PROJECT;

const client = new Opik({ projectName: PROJECT });

// One plain OpenAI client; each call is wrapped inside the task so it can be
// attached to the evaluation trace that runTests opens for that suite item.
const rawOpenAI = new OpenAI();

const { v1, v2 } = await syncPromptVersions(client);
const suite = await syncSuite(client, PROJECT);

// compareTo prints a coloured unified diff and returns it. Opik's prompt
// library renders the same v1 -> v2 diff in the UI.
console.log(`\nDiff ${PROMPT_NAME} v1 -> v2\n`);
const versions = await (await client.getPrompt({ name: PROMPT_NAME }))!.getVersions();
const byVersion = new Map(versions.map((v) => [v.version, v]));
byVersion.get("v2")!.compareTo(byVersion.get("v1")!);

const results: Record<string, { passRate: number | undefined; url?: string; failures: string[] }> = {};

for (const [label, prompt] of [["v1", v1], ["v2", v2]] as const) {
  // runTests runs the task over every suite item, has the judge check each
  // assertion, and logs one experiment per call. `prompts` links the experiment
  // to the exact prompt version, so the run is traceable back to its wording.
  const result = await runTests({
    testSuite: suite,
    experimentName: `${PROMPT_NAME}-${label}`,
    experimentConfig: { prompt_version: label, model: MODEL },
    prompts: [prompt],
    model: "gpt-4o-mini",
    projectName: PROJECT,
    task: async (item) => {
      const ep = item as unknown as EpisodeData;
      // trackOpenAI records the completion with model, token usage and cost.
      // Without `parent` it opens a separate trace per call; passing the task's
      // span keeps it inside the experiment item's own trace.
      const ctx = getTrackContext();
      const openai = trackOpenAI(rawOpenAI, {
        client,
        generationName: "write_title",
        parent: ctx?.span ?? ctx?.trace,
      });
      const title = await writeTitle(openai, prompt.prompt, ep);
      return { input: ep.notes, output: title };
    },
  });

  const failures: string[] = [];
  for (const item of result.itemResults.values()) {
    for (const t of item.testResults) {
      const failed = t.scoreResults.filter((s) => s.value !== 1).map((s) => s.name);
      const out = (t.testCase.taskOutput as { output?: string }).output;
      console.log(`  [${label}] ${item.passed ? "PASS" : "FAIL"}  "${out}"${failed.length ? "  <- " + failed.join("; ") : ""}`);
      failures.push(...failed);
    }
  }
  results[label] = { passRate: result.passRate, url: result.experimentUrl, failures };
  console.log(`${label}: ${result.itemsPassed}/${result.itemsTotal} items passed (${Math.round((result.passRate ?? 0) * 100)}%)\n`);
}

// flush drains the batched trace/span/experiment queues before the process exits.
await client.flush();
console.log("Summary", JSON.stringify(results, null, 2));
