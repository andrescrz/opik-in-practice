import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

function load<T>(file: string): T[] {
  return JSON.parse(readFileSync(fileURLToPath(new URL(`../data/${file}`, import.meta.url)), "utf8"));
}

export type RosterEntry = { area: string; name: string; role: string; contact: string; response_target: string; backup: string };
export type CareRecord = { animal: string; name: string; enclosure: string; area: string; age: number; weight_kg: number; diet: string; last_exam: string; conditions: string[]; baseline_notes: string; medications: string[] };
export type MaintenanceEntry = { enclosure: string; date: string; item: string; status: "open" | "closed" };

export const AREAS = ["veterinary", "hoofstock", "aquatics", "birds", "primates", "facilities"] as const;

const roster = load<RosterEntry>("roster.json");
const records = load<CareRecord>("care-records.json");
const maintenance = load<MaintenanceEntry>("maintenance-log.json");

export function lookupRoster(area: string): RosterEntry | { error: string } {
  return roster.find((r) => r.area === area.toLowerCase()) ?? { error: `No roster entry for "${area}". Valid areas: ${AREAS.join(", ")}.` };
}

export function lookupCareRecord(animal: string): CareRecord | { error: string } {
  const key = animal.toLowerCase().trim();
  return records.find((r) => r.animal === key || r.name.toLowerCase() === key) ?? { error: `No care record for "${animal}". Known animals: ${records.map((r) => r.animal).join(", ")}.` };
}

// Newest first, so a model reading a long log sees the latest state before older history.
export function lookupMaintenance(enclosure: string): MaintenanceEntry[] | { error: string } {
  const key = enclosure.toLowerCase().trim();
  const entries = maintenance.filter((m) => m.enclosure === key).sort((a, b) => b.date.localeCompare(a.date));
  return entries.length ? entries : { error: `No maintenance log for "${enclosure}". Known enclosures: ${[...new Set(maintenance.map((m) => m.enclosure))].join(", ")}.` };
}

// True when the "Call:" line of a triage answer names someone who is actually on the roster.
export function namesRosterPerson(answer: string): boolean {
  const line = answer.split("\n").find((l) => l.startsWith("Call:"));
  return !!line && roster.some((r) => line.includes(r.name));
}
