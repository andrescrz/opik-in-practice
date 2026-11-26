import { VoltAgentObservability } from "@voltagent/core";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
// Opik accepts OTLP as http/protobuf only; the http/json exporter is rejected with
// "400 Cannot find field: schemaUrl".
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";

type Attributes = Record<string, unknown>;

const providerFor = (model: string): string =>
  model.startsWith("claude") ? "anthropic" : model.startsWith("gemini") ? "google_ai" : "openai";

// VoltAgent labels spans with its own vocabulary (llm.model, llm.usage.prompt_tokens,
// input, ...). Opik only turns usage, model and cost into first-class fields when it
// finds the OpenTelemetry GenAI names, so we add those next to the originals.
export function mapToGenAI(attrs: Attributes): void {
  if (attrs["span.type"] === "llm") {
    const model = String(attrs["llm.model"] ?? "");
    if (model) {
      attrs["gen_ai.request.model"] = model;
      // Opik prices a span only when it knows both the provider and the model.
      attrs["gen_ai.provider.name"] = providerFor(model);
    }
    for (const kind of ["prompt_tokens", "completion_tokens", "total_tokens"]) {
      const value = attrs[`llm.usage.${kind}`];
      if (value !== undefined) attrs[`gen_ai.usage.${kind}`] = value;
    }
  } else if (attrs["span.type"] === "tool") {
    // Moves the call arguments to the GenAI name so the span is typed "tool" with them as input.
    attrs["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
    delete attrs["input"];
    // Serialized Zod internals; pure noise in the Opik UI.
    delete attrs["tool.parameters"];
  }
}

export class GenAIMappingExporter implements SpanExporter {
  constructor(private readonly inner: SpanExporter) {}

  export(spans: ReadableSpan[], done: Parameters<SpanExporter["export"]>[1]): void {
    for (const span of spans) mapToGenAI(span.attributes as Attributes);
    this.inner.export(spans, done);
  }

  shutdown(): Promise<void> {
    return this.inner.shutdown();
  }

  forceFlush(): Promise<void> {
    return this.inner.forceFlush?.() ?? Promise.resolve();
  }
}

const apiKey = process.env.OPIK_API_KEY;
const opikBase = (
  process.env.OPIK_URL_OVERRIDE ?? (apiKey ? "https://www.comet.com/opik/api" : "http://localhost:5173/api")
).replace(/\/+$/, "");

const otlp = new OTLPTraceExporter({
  url: `${opikBase}/v1/private/otel/v1/traces`,
  headers: {
    // projectName routes traces to this Opik project instead of "Default Project".
    projectName: process.env.OPIK_PROJECT_NAME ?? "voltagent-restaurant-reservations",
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
    ...(apiKey ? { Authorization: apiKey } : {}),
  },
});

// OPIK_GENAI_MAPPING=off sends VoltAgent's raw attributes, to compare what Opik shows without the mapping.
const mappingOn = process.env.OPIK_GENAI_MAPPING !== "off";

// BatchSpanProcessor ships finished spans to Opik in the background; every VoltAgent run
// becomes one trace, with agent, llm and tool spans, and no tracing code in the agent files.
export const observability = new VoltAgentObservability({
  serviceName: "voltagent-restaurant-reservations",
  spanProcessors: [new BatchSpanProcessor(mappingOn ? new GenAIMappingExporter(otlp) : otlp)],
});
