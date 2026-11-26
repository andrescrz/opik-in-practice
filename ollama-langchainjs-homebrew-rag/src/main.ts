import path from "node:path";
import { fileURLToPath } from "node:url";
import { OpikCallbackHandler } from "opik-langchain";
import { loadNearestEnv } from "./env.js";
import { buildAssistant } from "./rag.js";

const here = path.dirname(fileURLToPath(import.meta.url));
loadNearestEnv(path.resolve(here, ".."));

const PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? "ollama-langchainjs-homebrew-rag";

const QUESTIONS = [
  "How long must a lager rest at 16 C before it is lowered for lagering?",
  "What deposit do I owe to borrow the 30 litre kettle?",
  "Can I rinse the sanitiser off my fermenter after two minutes?",
];

async function main() {
  const baseUrl = process.env.OLLAMA_BASE_URL ?? "http://localhost:11434";
  const { chain } = await buildAssistant(path.resolve(here, "../docs"), baseUrl);

  // Turns every LangChain run into an Opik span (llm for ChatOllama, tool for the retriever,
  // general for the rest); the outermost run becomes the trace. Without it nothing is logged.
  const opikHandler = new OpikCallbackHandler({ projectName: PROJECT_NAME });

  for (const question of QUESTIONS) {
    console.log(`\nQ: ${question}`);
    // One invoke = one trace in the project, named by runName.
    const answer = await chain.invoke(question, {
      callbacks: [opikHandler],
      runName: "ask_the_handbook",
    });
    console.log(`A: ${answer}`);
  }

  // Traces upload in the background; without this a short script can exit before they arrive.
  await opikHandler.flushAsync();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
