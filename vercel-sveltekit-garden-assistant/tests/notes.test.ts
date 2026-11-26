import { describe, expect, it } from "vitest";
import { buildSystemPrompt, loadNotes, retrieve } from "../src/lib/server/notes";

const notes = loadNotes();

describe("plot notes", () => {
  it("loads every note in data/", () => {
    expect(notes.map((n) => n.name)).toContain("pest-id-guide");
    expect(notes.length).toBe(6);
  });

  it("finds the pest guide for an aphid question", () => {
    const top = retrieve("tiny green insects, sticky leaves, aphids on my beans", notes, 1);
    expect(top[0].name).toBe("pest-id-guide");
  });

  it("finds the tomato notes for a blight question", () => {
    const top = retrieve("brown patches with yellow halo on tomato leaves", notes, 1);
    expect(top[0].name).toBe("tomato-notes");
  });

  it("returns nothing when no note overlaps", () => {
    expect(retrieve("zzz qqq", notes)).toEqual([]);
  });

  it("puts retrieved notes into the system prompt", () => {
    expect(buildSystemPrompt(notes.slice(0, 1))).toContain(notes[0].text);
    expect(buildSystemPrompt([])).toContain("(no matching notes)");
  });
});
