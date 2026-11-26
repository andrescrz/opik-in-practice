import './env';
import { SpanStatusCode, trace } from '@opentelemetry/api';
import { Client, Connection } from '@temporalio/client';
import { OpenTelemetryWorkflowClientInterceptor } from '@temporalio/interceptors-opentelemetry';
import { APPLICATIONS } from './applications';
import { setupTracing } from './tracing';
import { TASK_QUEUE } from './types';
import type { reviewApplication } from './workflows';

export async function reviewAll(address: string): Promise<void> {
  // Client side of the distributed trace: exports to the same Opik project as the worker.
  const tracing = setupTracing('grant-client');
  const connection = await Connection.connect({ address });
  // The client interceptor injects the active trace context into the workflow headers;
  // the worker reads it from there. This is the link between the two processes.
  const client = new Client({ connection, interceptors: { workflow: [new OpenTelemetryWorkflowClientInterceptor()] } });
  const tracer = trace.getTracer('grant-client');
  try {
    for (const app of APPLICATIONS) {
      console.log(`\n=== ${app.id}: ${app.projectTitle}`);
      // Root span of the Opik trace; the worker's workflow and activity spans nest beneath it.
      await tracer.startActiveSpan(`review:${app.id}`, async (span) => {
        try {
          span.setAttributes({ 'input.value': JSON.stringify(app), 'input.mime_type': 'application/json' });
          const handle = await client.workflow.start<typeof reviewApplication>('reviewApplication', {
            taskQueue: TASK_QUEUE,
            workflowId: `review-${app.id}`,
            args: [app],
          });
          const outcome = await handle.result();
          span.setAttributes({ 'output.value': JSON.stringify(outcome), 'output.mime_type': 'application/json' });
          span.setStatus({ code: SpanStatusCode.OK });
          console.log(`Verdict: ${outcome.verdict}`);
          console.log(`Summary: ${outcome.summary}`);
        } catch (err) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
          throw err;
        } finally {
          span.end();
        }
      });
    }
  } finally {
    await connection.close();
    await tracing?.provider.shutdown(); // flush the client's spans to Opik before exit
  }
}

if (require.main === module) {
  reviewAll(process.env.TEMPORAL_ADDRESS ?? 'localhost:7233').catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
