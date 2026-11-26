import { describe, expect, it } from "vitest";
import { OpikExporter } from "opik-vercel";

// With OPIK_TRACK_DISABLE=true the Opik client never sends anything, so the exporter and
// telemetry settings can be exercised in unit tests without a server or keys.
describe("opik-vercel settings", () => {
  it("builds telemetry settings that carry the trace name", () => {
    const settings = OpikExporter.getSettings({ name: "garden-chat-turn" });
    expect(settings.isEnabled).toBe(true);
    expect(settings.metadata?.traceName).toBe("garden-chat-turn");
  });

  it("constructs an exporter and shuts it down with tracking disabled", async () => {
    const exporter = new OpikExporter();
    await expect(exporter.forceFlush()).resolves.toBeUndefined();
    await expect(exporter.shutdown()).resolves.toBeUndefined();
  });
});
