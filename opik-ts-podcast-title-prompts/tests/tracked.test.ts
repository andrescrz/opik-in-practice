import { describe, expect, it } from "vitest";

// Documented switch: with tracking disabled the SDK's track() wrapper is a
// pass-through, so traced code stays testable without an Opik server.
process.env.OPIK_TRACK_DISABLE = "true";

describe("tracked function with tracking disabled", () => {
  it("still returns the function's result", async () => {
    const { track } = await import("opik");
    const { writeTitle } = await import("../src/titles.js");
    const { EPISODES } = await import("../src/episodes.js");
    const client = {
      chat: { completions: { create: async () => ({ choices: [{ message: { content: "Okay Title" } }] }) } },
    } as never;
    const traced = track({ name: "write_title" }, (system: string) => writeTitle(client, system, EPISODES[0]!));
    expect(await traced("any system prompt")).toBe("Okay Title");
  });
});
