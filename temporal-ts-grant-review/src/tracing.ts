import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { ATTR_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import './env';

export const OPIK_PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? 'temporal-ts-grant-review';

export function trackingDisabled(): boolean {
  return process.env.OPIK_TRACK_DISABLE === 'true';
}

export interface Tracing {
  provider: NodeTracerProvider;
  exporter: OTLPTraceExporter;
  resource: Resource;
}

/**
 * Point this process's OpenTelemetry spans at Opik's OTLP endpoint.
 * Both the client and the worker call this with the same project name, so the
 * spans each process produces are stitched into one Opik trace. The
 * `projectName` header is what routes them to the right project.
 */
export function setupTracing(serviceName: string): Tracing | undefined {
  if (trackingDisabled()) return undefined;
  const base = (process.env.OPIK_URL_OVERRIDE ?? 'https://www.comet.com/opik/api').replace(/\/+$/, '');
  const headers: Record<string, string> = {
    'Comet-Workspace': process.env.OPIK_WORKSPACE ?? 'default',
    projectName: OPIK_PROJECT_NAME,
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY; // Opik Cloud only
  const exporter = new OTLPTraceExporter({ url: `${base}/v1/private/otel/v1/traces`, headers });
  const resource = new Resource({ [ATTR_SERVICE_NAME]: serviceName });
  const provider = new NodeTracerProvider({ resource });
  provider.addSpanProcessor(new BatchSpanProcessor(exporter));
  provider.register();
  return { provider, exporter, resource };
}
