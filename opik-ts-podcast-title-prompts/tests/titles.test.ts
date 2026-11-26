import { describe, expect, it } from "vitest";
import { EPISODES } from "../src/episodes.js";
import { GLOBAL_ASSERTIONS, V1, V2, guestAssertion } from "../src/prompts.js";
import { cleanTitle, episodeMessage, writeTitle } from "../src/titles.js";

const stubClient = (reply: string | null) =>
  ({
    chat: { completions: { create: async () => ({ choices: [{ message: { content: reply } }] }) } },
  }) as never;

describe("titles", () => {
  it("trims whitespace but keeps the model's own characters", () => {
    expect(cleanTitle('  "Hello"\n')).toBe('"Hello"');
    expect(cleanTitle(null)).toBe("");
  });

  it("puts show and notes into the user message", () => {
    const msg = episodeMessage(EPISODES[0]!);
    expect(msg).toContain("Show: Tidewater Tales");
    expect(msg).toContain("Marisol Okafor");
  });

  it("returns the cleaned completion", async () => {
    expect(await writeTitle(stubClient("  A Plain Title \n"), V2.text, EPISODES[1]!)).toBe("A Plain Title");
  });
});

describe("prompt data", () => {
  it("v2 differs from v1 so the library records a new version", () => {
    expect(V2.text).not.toBe(V1.text);
  });

  it("every guest episode gets an assertion naming that guest", () => {
    const guests = EPISODES.filter((e) => e.guest);
    expect(guests.length).toBeGreaterThan(0);
    for (const e of guests) expect(guestAssertion(e.guest!)).toContain(e.guest);
    expect(GLOBAL_ASSERTIONS.length).toBeGreaterThan(2);
  });
});
