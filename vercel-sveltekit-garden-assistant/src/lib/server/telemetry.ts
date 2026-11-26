import "./env";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";

export const PROJECT_NAME = process.env.OPIK_PROJECT_NAME || "vercel-sveltekit-garden-assistant";

// Vite re-evaluates server modules on edits; the global guard keeps us from registering twice.
const state = globalThis as typeof globalThis & { __opikTelemetryStarted?: boolean };

if (!state.__opikTelemetryStarted) {
  state.__opikTelemetryStarted = true;

  const client = new Opik({ projectName: PROJECT_NAME });

  // OpikExporter turns the AI SDK's OpenTelemetry spans into Opik traces and spans.
  // Without a running OTel SDK holding this exporter, nothing leaves the process.
  const sdk = new NodeSDK({
    serviceName: PROJECT_NAME,
    traceExporter: new OpikExporter({ client, tags: ["sveltekit", "streaming"] }),
  });
  sdk.start();

  // AI SDK v7 only emits spans after an explicit registerTelemetry call (v4-v6 emitted them by default).
  // enrichSpan copies the chat id from runtimeContext onto the span as the metadata Opik reads as the
  // thread id (folding a conversation's turns into one thread), and traceName as the trace's name
  // (otherwise v7 traces are all called "invoke_agent <model>").
  registerTelemetry(
    new OpenTelemetry({
      usage: true,
      enrichSpan: ({ runtimeContext }) => {
        const attributes: Record<string, string> = {};
        if (runtimeContext?.threadId != null) {
          attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
        }
        if (runtimeContext?.traceName != null) {
          attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
        }
        return attributes;
      },
    }),
  );

  // The exporter batches spans; flush on shutdown so a Ctrl-C does not drop the last turn.
  const shutdown = async () => {
    await sdk.shutdown();
    await client.flush();
  };
  process.once("SIGTERM", shutdown);
  process.once("SIGINT", shutdown);
}
