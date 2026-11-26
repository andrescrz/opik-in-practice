// Plays three scripted member requests through the assistant.
import { config } from "dotenv";
import { findUpSync } from "./env.ts";

config({ path: findUpSync(".env"), quiet: true });

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { mastra } = await import("./mastra.ts");

const REQUESTS = [
  "Hi, I'm Priya (checking account CHK-2041-01). What's my balance?",
  "Can you show my last three transactions on CHK-2041-01? I don't recognise the electronics one.",
  "I'm Declan, account CHK-3318-01. There are two $200 ATM withdrawals in Lisbon and I'm not abroad. Please freeze my card.",
];

const agent = mastra.getAgent("bankingAgent");

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Member: ${request}`);
  const result = await agent.generate(request, { maxSteps: 6 });
  console.log(`Agent:  ${result.text}`);
}

await mastra.shutdown();
