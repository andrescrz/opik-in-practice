import { describe, expect, it } from "vitest";
import { ReservationBook } from "../src/reservations.ts";
import { buildTools } from "../src/tools.ts";
import { GenAIMappingExporter, mapToGenAI } from "../src/observability.ts";

describe("tools without tracing", () => {
  // No VoltAgent instance and no exporter are registered here: tools are plain functions,
  // so the tracing layer never gets in the way of unit tests.
  it("runs book_table directly", async () => {
    const tool = buildTools(new ReservationBook()).find((t) => t.name === "book_table")! as any;
    const result = await tool.execute({ guest_name: "Rosa", date: "2026-12-13", time: "19:00", party_size: 2 }, undefined as never);
    expect(result).toMatchObject({ ok: true, booking: { id: "LF-1007" } });
  });
});

describe("mapToGenAI", () => {
  it("copies VoltAgent usage and model to gen_ai.* names with a provider", () => {
    const attrs: Record<string, unknown> = {
      "span.type": "llm",
      "llm.model": "gpt-4o-mini",
      "llm.usage.prompt_tokens": 590,
      "llm.usage.completion_tokens": 35,
      "llm.usage.total_tokens": 625,
    };
    mapToGenAI(attrs);
    expect(attrs).toMatchObject({
      "gen_ai.request.model": "gpt-4o-mini",
      "gen_ai.provider.name": "openai",
      "gen_ai.usage.prompt_tokens": 590,
      "gen_ai.usage.completion_tokens": 35,
      "gen_ai.usage.total_tokens": 625,
    });
  });

  it("moves tool arguments to gen_ai.tool.call.arguments", () => {
    const attrs: Record<string, unknown> = { "span.type": "tool", input: '{"booking_id":"LF-1002"}', "tool.parameters": "{}" };
    mapToGenAI(attrs);
    expect(attrs["gen_ai.tool.call.arguments"]).toBe('{"booking_id":"LF-1002"}');
    expect(attrs).not.toHaveProperty("input");
    expect(attrs).not.toHaveProperty("tool.parameters");
  });

  it("maps spans on their way to the inner exporter", () => {
    const seen: Record<string, unknown>[] = [];
    const inner = { export: (spans: any[], cb: any) => { seen.push(...spans.map((s) => s.attributes)); cb({ code: 0 }); }, shutdown: async () => {} };
    const span = { attributes: { "span.type": "llm", "llm.model": "claude-haiku-4-5", "llm.usage.total_tokens": 5 } };
    new GenAIMappingExporter(inner as any).export([span as any], () => {});
    expect(seen[0]).toMatchObject({ "gen_ai.provider.name": "anthropic", "gen_ai.usage.total_tokens": 5 });
  });
});
