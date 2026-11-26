import { afterAll, expect, it } from "vitest";

// OTEL_SDK_DISABLED is the OpenTelemetry-standard switch: the NodeSDK does not start, no exporter is created,
// and instrumented code runs exactly as it would without tracing.
process.env.OTEL_SDK_DISABLED = "true";
const { shutdownTracing } = await import("../src/instrumentation.ts");
const { rosterTool, careRecordTool } = await import("../src/tools.ts");

afterAll(() => shutdownTracing());

it("runs an instrumented BeeAI tool with tracing disabled", async () => {
  const out = await rosterTool.run({ area: "aquatics" });
  expect(out.getTextContent()).toContain("Odalys Pike");
});

it("returns the error payload for an unknown animal", async () => {
  const out = await careRecordTool.run({ animal: "unicorn" });
  expect(out.getTextContent()).toContain("No care record");
});
