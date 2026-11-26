import path from "node:path";
import { describe, expect, it } from "vitest";
import { cosine, formatContext, HandbookRetriever, loadHandbook, splitHandbook } from "../src/handbook.js";

const DOCS = path.resolve(import.meta.dirname, "../docs");

describe("handbook chunking", () => {
  it("splits a file into one chunk per section with the title attached", () => {
    const chunks = splitHandbook("x.md", "# Title\n\n## One\nfoo\n\n## Two\nbar\n");
    expect(chunks.map((c) => c.metadata.section)).toEqual(["One", "Two"]);
    expect(chunks[0]!.pageContent).toBe("Title\n\n## One\nfoo");
  });

  it("loads every section of the shipped docs", async () => {
    const chunks = await loadHandbook(DOCS);
    expect(chunks).toHaveLength(12);
  });
});

describe("retrieval", () => {
  it("ranks by cosine similarity and returns k chunks", async () => {
    const chunks = splitHandbook("x.md", "# T\n\n## Cider\ncider\n\n## Kettle\nkettle\n\n## Stout\nstout\n");
    const words = ["cider", "kettle", "stout"];
    const embed = (t: string) => words.map((w) => (t.includes(w) ? 1 : 0));
    const embeddings = {
      embedDocuments: async (ts: string[]) => ts.map(embed),
      embedQuery: async (t: string) => embed(t),
    };
    const retriever = await HandbookRetriever.build(chunks, embeddings, 1);
    const docs = await retriever.invoke("what about the kettle");
    expect(docs).toHaveLength(1);
    expect(formatContext(docs)).toContain("kettle");
  });

  it("scores identical vectors 1 and orthogonal vectors 0", () => {
    expect(cosine([1, 2], [1, 2])).toBeCloseTo(1);
    expect(cosine([1, 0], [0, 1])).toBe(0);
  });
});
