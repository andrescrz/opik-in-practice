import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { Document } from "@langchain/core/documents";
import type { EmbeddingsInterface } from "@langchain/core/embeddings";
import { BaseRetriever } from "@langchain/core/retrievers";

// One chunk per "## " section: each chunk is a single rule, which keeps the
// prompt short enough for a 1B model on CPU.
export function splitHandbook(file: string, markdown: string): Document[] {
  const [title = "", ...sections] = markdown.split(/\n## /);
  return sections.map(
    (section) =>
      new Document({
        pageContent: `${title.replace(/^# /, "").trim()}\n\n## ${section.trim()}`,
        metadata: { source: file, section: section.split("\n")[0]?.trim() },
      }),
  );
}

export async function loadHandbook(docsDir: string): Promise<Document[]> {
  const files = (await readdir(docsDir)).filter((f) => f.endsWith(".md")).sort();
  const chunks: Document[] = [];
  for (const file of files) {
    chunks.push(...splitHandbook(file, await readFile(path.join(docsDir, file), "utf8")));
  }
  return chunks;
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i]! * b[i]!;
    na += a[i]! ** 2;
    nb += b[i]! ** 2;
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

// A tiny in-memory vector retriever: embeds every chunk once, then ranks by
// cosine similarity to the question.
export class HandbookRetriever extends BaseRetriever {
  lc_namespace = ["homebrew", "retrievers"];

  constructor(
    private readonly chunks: Document[],
    private readonly vectors: number[][],
    private readonly embeddings: EmbeddingsInterface,
    private readonly k: number,
  ) {
    super();
  }

  static async build(
    chunks: Document[],
    embeddings: EmbeddingsInterface,
    k: number,
  ): Promise<HandbookRetriever> {
    const vectors = await embeddings.embedDocuments(chunks.map((c) => c.pageContent));
    return new HandbookRetriever(chunks, vectors, embeddings, k);
  }

  async _getRelevantDocuments(query: string): Promise<Document[]> {
    const q = await this.embeddings.embedQuery(query);
    return this.vectors
      .map((v, i) => ({ i, score: cosine(q, v) }))
      .sort((x, y) => y.score - x.score)
      .slice(0, this.k)
      .map(({ i }) => this.chunks[i]!);
  }
}

export function formatContext(docs: Document[]): string {
  return docs.map((d) => d.pageContent).join("\n\n---\n\n");
}
