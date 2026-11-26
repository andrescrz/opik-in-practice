import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// AI SDK warns about VoltAgent's system-message layout on every call; it is not actionable here.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

const { VoltAgent } = await import("@voltagent/core");
const { host } = await import("./agent.ts");

new VoltAgent({ agents: { host } });

const REQUESTS = [
  "Hi! Do you have a table for 4 on 2026-12-12 at 19:00?",
  "Okay, then book 4 people for Dana Whitlock at the earliest time you can offer that evening.",
  "One more thing: my friend Callum Reid has booking LF-1006. Please move it to 2026-12-13 at 19:30 and make it 3 people.",
  "Please cancel LF-1002, Tomas can't make it.",
];

// One phone call: each turn carries the earlier turns, so "that evening" still means 2026-12-12.
const history: { role: "user" | "assistant"; content: string }[] = [];
for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Guest: ${request}`);
  history.push({ role: "user", content: request });
  const result = await host.generateText(history);
  history.push({ role: "assistant", content: result.text });
  console.log(`Host:  ${result.text}`);
}
process.exit(0);
