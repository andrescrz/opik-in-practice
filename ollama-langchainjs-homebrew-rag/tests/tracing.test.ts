import { FakeListChatModel } from "@langchain/core/utils/testing";
import { track } from "opik";
import { OpikCallbackHandler } from "opik-langchain";
import { describe, expect, it } from "vitest";

// Documented switch: with tracking disabled the SDK's track() wrapper is a pass-through.
process.env.OPIK_TRACK_DISABLE = "true";

import { splitHandbook, HandbookRetriever } from "../src/handbook.js";
import { buildChain } from "../src/rag.js";

const chunks = splitHandbook("x.md", "# T\n\n## Kettle\nkettle deposit is 40 euro\n\n## Cider\ncider\n");
const embed = (t: string) => [t.includes("kettle") ? 1 : 0, t.includes("cider") ? 1 : 0];
const embeddings = {
  embedDocuments: async (ts: string[]) => ts.map(embed),
  embedQuery: async (t: string) => embed(t),
};

describe("chain with a stubbed model", () => {
  it("answers without any handler attached", async () => {
    const retriever = await HandbookRetriever.build(chunks, embeddings, 1);
    const chain = buildChain(retriever, new FakeListChatModel({ responses: ["40 euro"] }));
    expect(await chain.invoke("kettle deposit?")).toBe("40 euro");
  });

  it("runs inside an SDK track() wrapper with tracking disabled", async () => {
    const retriever = await HandbookRetriever.build(chunks, embeddings, 1);
    const chain = buildChain(retriever, new FakeListChatModel({ responses: ["40 euro"] }));
    const traced = track({ name: "ask", type: "general" }, (q: string) => chain.invoke(q));
    expect(await traced("kettle deposit?")).toBe("40 euro");
  });

  it("surfaces retrieval as a named span when the Opik handler is attached", async () => {
    const spans: string[] = [];
    const fakeSpan = (name: string) => {
      spans.push(name);
      return { span: (o: { name: string }) => fakeSpan(o.name), update: () => {} };
    };
    const client = { trace: (o: { name: string }) => fakeSpan(o.name), config: {}, flush: async () => {} };
    const handler = new OpikCallbackHandler({ client: client as never });

    const retriever = await HandbookRetriever.build(chunks, embeddings, 1);
    const chain = buildChain(retriever, new FakeListChatModel({ responses: ["40 euro"] }));
    await chain.invoke("kettle deposit?", { callbacks: [handler], runName: "ask_the_handbook" });

    expect(spans).toContain("search_handbook");
  });
});
