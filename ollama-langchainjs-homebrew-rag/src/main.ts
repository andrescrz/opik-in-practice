import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadNearestEnv } from "./env.js";
import { buildAssistant } from "./rag.js";

const here = path.dirname(fileURLToPath(import.meta.url));
loadNearestEnv(path.resolve(here, ".."));

const QUESTIONS = [
  "How long must a lager rest at 16 C before it is lowered for lagering?",
  "What deposit do I owe to borrow the 30 litre kettle?",
  "Can I rinse the sanitiser off my fermenter after two minutes?",
];

async function main() {
  const baseUrl = process.env.OLLAMA_BASE_URL ?? "http://localhost:11434";
  const { chain } = await buildAssistant(path.resolve(here, "../docs"), baseUrl);

  for (const question of QUESTIONS) {
    console.log(`\nQ: ${question}`);
    console.log(`A: ${await chain.invoke(question)}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
