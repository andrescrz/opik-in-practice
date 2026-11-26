import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({ path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))], quiet: true });

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Tracing must start before BeeAI is imported, and only after the env vars above are loaded.
const { shutdownTracing } = await import("./instrumentation.ts");
const { triage } = await import("./agent.ts");
const { namesRosterPerson } = await import("./lookups.ts");

const REQUESTS = [
  "Juniper the giraffe hasn't touched her morning browse and is standing by the fence.",
  "Alarm on the penguin pool filter just went off, birds are bunching up at the far end.",
  "Biscuit the red panda is quiet this morning, curled up on the platform.",
];

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===\nKeeper: ${request}`);
  const answer = await triage(request);
  console.log(answer);
  console.log(`(named person is on the roster: ${namesRosterPerson(answer)})`);
}

await shutdownTracing();
console.log(`\nDone. Open the "${process.env.OPIK_PROJECT_NAME ?? "beeai-zoo-care-triage"}" project in Opik.`);
