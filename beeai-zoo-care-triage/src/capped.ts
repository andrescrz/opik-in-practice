// Same penguin alarm as the demo, but with the ReAct loop capped at 2 iterations: the agent
// cannot reach the roster lookup, so the trace shows an incomplete loop.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({ path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))], quiet: true });

const { shutdownTracing } = await import("./instrumentation.ts");
const { triage, DEFAULT_LIMITS } = await import("./agent.ts");

try {
  console.log(await triage("Alarm on the penguin pool filter just went off, birds are bunching up at the far end.", { ...DEFAULT_LIMITS, maxIterations: 2 }));
} catch (err) {
  console.log(`Agent gave up: ${(err as Error).message}`);
}

await shutdownTracing();
