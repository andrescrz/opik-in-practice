import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnableLambda } from "@langchain/core/runnables";
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

export async function buildAssistant(docsDir: string, baseUrl: string) {
  const embeddings = new OllamaEmbeddings({ model: EMBED_MODEL, baseUrl });
  const retriever = await HandbookRetriever.build(await loadHandbook(docsDir), embeddings, K);

  const llm = new ChatOllama({ model: CHAT_MODEL, baseUrl, temperature: 0, numPredict: 250 });

  const searchHandbook = async (question: string) =>
    formatContext(await retriever.invoke(question));

  const chain = RunnableLambda.from(async (question: string) => ({
    context: await searchHandbook(question),
    question,
  }))
    .pipe(prompt)
    .pipe(llm)
    .pipe(new StringOutputParser());

  return { chain };
}
