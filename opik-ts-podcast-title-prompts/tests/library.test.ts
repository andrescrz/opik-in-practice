import { describe, expect, it } from "vitest";
import { syncPromptVersions } from "../src/library.js";
import { V1, V2 } from "../src/prompts.js";

function fakeClient(initial: string[]) {
  const texts = [...initial];
  const prompt = (version?: string) => ({
    prompt: texts[Number((version ?? `v${texts.length}`).slice(1)) - 1],
    getVersions: async () => texts.map((t) => ({ prompt: t })),
  });
  return {
    texts,
    getPrompt: async ({ version }: { version?: string }) => (texts.length ? prompt(version) : null),
    createPrompt: async ({ prompt: p }: { prompt: string }) => void texts.push(p),
  };
}

describe("syncPromptVersions", () => {
  it("creates v1 and v2 on a fresh server", async () => {
    const c = fakeClient([]);
    await syncPromptVersions(c as never);
    expect(c.texts).toEqual([V1.text, V2.text]);
  });

  it("does not append a third version when both already exist", async () => {
    const c = fakeClient([V1.text, V2.text]);
    await syncPromptVersions(c as never);
    expect(c.texts).toHaveLength(2);
  });
});
