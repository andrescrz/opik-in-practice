import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { bankingAgent } from "./agent.ts";

// Default to a local self-hosted Opik; point OPIK_URL_OVERRIDE at Opik Cloud
// (https://www.comet.com/opik/api) and set OPIK_API_KEY to send it there.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");
const project = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";

export const mastra = new Mastra({
  agents: { bankingAgent },
  observability: new Observability({
    configs: {
      default: {
        serviceName: project,
        exporters: [
          // OtelExporter turns Mastra's agent/LLM/tool events into OpenTelemetry spans and
          // POSTs them to Opik's OTLP endpoint: one trace per agent.generate() call, with
          // invoke_agent > agent_step > chat / execute_tool children and no tracing code elsewhere.
          new OtelExporter({
            provider: {
              custom: {
                endpoint: `${opikBase}/v1/private/otel/v1/traces`,
                // Opik's OTLP endpoint rejects Mastra's JSON payload (400, "Cannot find field: schemaUrl"),
                // so spans must go as protobuf; without this nothing arrives and no project is created.
                protocol: "http/protobuf",
                headers: {
                  // Selects the Opik workspace the spans are ingested into.
                  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
                  // Routes the traces into this Opik project instead of "Default Project".
                  projectName: project,
                  // Only Opik Cloud needs a key; a local install takes none.
                  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
                },
              },
            },
          }),
        ],
      },
    },
  }),
});
