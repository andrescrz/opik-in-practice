import { expect, it } from "vitest";

// Importing the Mastra instance builds the Opik OtelExporter config but sends
// nothing until an agent runs, so the traced setup is harmless in unit tests.
// Point it at a dead port to prove no spans are needed for the app to load.
it("builds the traced Mastra instance without contacting Opik", async () => {
  process.env.OPIK_URL_OVERRIDE = "http://127.0.0.1:9/api";
  const { mastra } = await import("../src/mastra.ts");
  expect(mastra.getAgent("bankingAgent").name).toBe("harbor-pines-assistant");
  expect(Object.keys(await mastra.getAgent("bankingAgent").listTools())).toEqual([
    "getBalance",
    "getRecentTransactions",
    "freezeCard",
  ]);
});
