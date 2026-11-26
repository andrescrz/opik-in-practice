// Wires BeeAI to Opik over plain OpenTelemetry; no Opik SDK is involved.
// BeeAIInstrumentation emits OpenInference spans (agent run, ReAct iteration, LLM call, tool call);
// Opik's OTLP endpoint turns them into one trace per agent.run() with typed spans underneath.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { BatchSpanProcessor, type Span, type SpanProcessor } from "@opentelemetry/sdk-trace-base";
import { MODEL, PROVIDER } from "./config.ts";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { BeeAIInstrumentation } from "@arizeai/openinference-instrumentation-beeai";
import * as beeaiFramework from "beeai-framework";

const PROJECT = process.env.OPIK_PROJECT_NAME ?? "beeai-zoo-care-triage";
const apiBase = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");

const headers: Record<string, string> = {
  // The projectName header decides which Opik project receives the traces; without it they land in "Default Project".
  projectName: PROJECT,
  // Workspace routing; required on self-hosted and Cloud alike.
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
};
// Only Opik Cloud needs an API key; a local stack takes no Authorization header.
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

const beeAI = new BeeAIInstrumentation();

// The instrumentation puts the model name on the LLM "start" span but token usage on the "success" span, and never
// reports the provider. Opik computes cost only when one span carries usage + provider + model, so every
// chat span is stamped with all three identifiers; without this the usage shows up but cost stays null.
const stampModel: SpanProcessor = {
  onStart(span: Span) {
    if (span.name.startsWith("backend.openai.chat")) {
      span.setAttribute("gen_ai.system", PROVIDER);
      span.setAttribute("llm.model_name", MODEL);
    }
  },
  onEnd() {},
  forceFlush: async () => {},
  shutdown: async () => {},
};

const exporter = new OTLPTraceExporter({
  // The protobuf exporter is required: Opik rejects OTLP/JSON from JS exporters with "Cannot find field: schemaUrl".
  url: `${apiBase}/v1/private/otel/v1/traces`,
  headers,
});

const sdk = new NodeSDK({
  spanProcessors: [stampModel, new BatchSpanProcessor(exporter)],
  instrumentations: [beeAI],
});
sdk.start();

// tsx/ESM loads beeai-framework before the instrumentation's module hook can patch it;
// without this call the agent runs normally but emits no spans at all.
beeAI.manuallyInstrument(beeaiFramework);

// shutdown() flushes the batch span processor; skipping it drops the last request's spans when the process exits.
export const shutdownTracing = () => sdk.shutdown();
