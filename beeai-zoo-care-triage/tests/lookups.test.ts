import { describe, expect, it } from "vitest";
import { lookupCareRecord, lookupMaintenance, lookupRoster, namesRosterPerson } from "../src/lookups.ts";

describe("lookups", () => {
  it("finds a care record by species or by name, case-insensitively", () => {
    expect(lookupCareRecord("Giraffe")).toMatchObject({ enclosure: "savanna-yard" });
    expect(lookupCareRecord("biscuit")).toMatchObject({ animal: "red panda" });
  });

  it("returns an error object listing valid values instead of throwing", () => {
    expect(lookupCareRecord("dragon")).toHaveProperty("error");
    expect(lookupRoster("astronomy")).toHaveProperty("error");
  });

  it("returns the maintenance log newest first, with open items visible", () => {
    const log = lookupMaintenance("polar-cove");
    expect(Array.isArray(log)).toBe(true);
    const entries = log as { date: string; status: string }[];
    expect(entries[0].date >= entries[1].date).toBe(true);
    expect(entries.some((e) => e.status === "open")).toBe(true);
  });

  it("flags answers whose Call line names someone off the roster", () => {
    expect(namesRosterPerson("Urgency: emergency\nCall: Odalys Pike (radio ch. 7)")).toBe(true);
    expect(namesRosterPerson("Urgency: emergency\nCall: Dr. Nobody (ext. 9999)")).toBe(false);
  });
});
