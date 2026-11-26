import type { BaseChatModel } from "@langchain/core/language_models/chat_models";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnableLambda, type RunnableConfig } from "@langchain/core/runnables";
import { ChatOllama, OllamaEmbeddings } from "@langchain/ollama";
import { formatContext, HandbookRetriever, loadHandbook } from "./handbook.js";

export const CHAT_MODEL = "llama3.2:1b";
export const EMBED_MODEL = "nomic-embed-text";
export const K = 2;

export const prompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    "You are the Copperkettle Brewers' handbook assistant. Answer using only the " +
      "excerpts below. If they do not cover the question, say so. Answer in at most " +
      "three sentences.\n\n{context}",
  ],
  ["human", "{question}"],
]);

export function buildChain(retriever: HandbookRetriever, llm: BaseChatModel) {
  // Retrieval is its own named step. Forwarding `config` hands the Opik callback handler to the
  // retriever run: a bare retriever.invoke(question) inside a lambda silently drops the retrieval
  // span. runName shows it as "search_handbook" (a tool span) between the lambda and the prompt.
  const searchHandbook = async (question: string, config?: RunnableConfig) =>
    formatContext(await retriever.invoke(question, { ...config, runName: "search_handbook" }));

  return RunnableLambda.from(async (question: string, config?: RunnableConfig) => ({
    context: await searchHandbook(question, config),
    question,
  }))
    .pipe(prompt)
    .pipe(llm)
    .pipe(new StringOutputParser());
}

export async function buildAssistant(docsDir: string, baseUrl: string) {
  const embeddings = new OllamaEmbeddings({ model: EMBED_MODEL, baseUrl });
  const retriever = await HandbookRetriever.build(await loadHandbook(docsDir), embeddings, K);
  const llm = new ChatOllama({ model: CHAT_MODEL, baseUrl, temperature: 0, numPredict: 250 });
  return { chain: buildChain(retriever, llm) };
}
