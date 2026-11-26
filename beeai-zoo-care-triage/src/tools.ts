import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { AREAS, lookupCareRecord, lookupMaintenance, lookupRoster } from "./lookups.ts";

export const rosterTool = new DynamicTool({
  name: "lookup_roster",
  description: `Find the on-call vet or keeper for a care area. Valid areas: ${AREAS.join(", ")}.`,
  inputSchema: z.object({ area: z.enum(AREAS).describe("Care area to find the on-call person for.") }),
  async handler({ area }) {
    return new JSONToolOutput(lookupRoster(area));
  },
});

export const careRecordTool = new DynamicTool({
  name: "get_care_record",
  description: "Get an animal's care record: age, diet, medications, known conditions, last exam, and normal behaviour. Pass the species (e.g. giraffe) or the animal's name.",
  inputSchema: z.object({ animal: z.string().describe("Species or individual name.") }),
  async handler({ animal }) {
    return new JSONToolOutput(lookupCareRecord(animal));
  },
});

export const maintenanceTool = new DynamicTool({
  name: "get_maintenance_log",
  description: "Get recent maintenance entries (newest first, with open/closed status) for an enclosure id such as savanna-yard, polar-cove, canopy-ridge, wetland-bank, kelp-tank.",
  inputSchema: z.object({ enclosure: z.string().describe("Enclosure id from the animal's care record.") }),
  async handler({ enclosure }) {
    return new JSONToolOutput(lookupMaintenance(enclosure));
  },
});

export const tools = [rosterTool, careRecordTool, maintenanceTool];
