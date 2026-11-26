import './env';
import { NativeConnection, Worker } from '@temporalio/worker';
import {
  OpenTelemetryActivityInboundInterceptor,
  OpenTelemetryActivityOutboundInterceptor,
  makeWorkflowExporter,
} from '@temporalio/interceptors-opentelemetry';
import * as activities from './activities';
import { setupTracing } from './tracing';
import { TASK_QUEUE } from './types';

async function main() {
  // Second OS process, same Opik project as the client: its spans join the client's trace.
  const tracing = setupTracing('grant-worker');
  const address = process.env.TEMPORAL_ADDRESS ?? 'localhost:7233';
  const connection = await NativeConnection.connect({ address });
  const worker = await Worker.create({
    connection,
    taskQueue: TASK_QUEUE,
    workflowsPath: require.resolve('./workflows'),
    activities,
    // Workflow code runs in a sandbox with no network, so its spans leave through this sink
    // and are exported by the same exporter as the activity spans.
    sinks: tracing ? { exporter: makeWorkflowExporter(tracing.exporter, tracing.resource) } : undefined,
    interceptors: {
      workflowModules: tracing ? [require.resolve('./workflows/interceptors')] : [],
      // One RunActivity span per attempt: this is what shows the failed try next to the retry.
      activity: tracing
        ? [
            (ctx) => ({
              inbound: new OpenTelemetryActivityInboundInterceptor(ctx),
              outbound: new OpenTelemetryActivityOutboundInterceptor(ctx),
            }),
          ]
        : [],
    },
  });
  console.log(`WORKER_READY on ${address}, task queue "${TASK_QUEUE}"`);
  await worker.run();
  await connection.close();
  // Without this flush the last spans (the final activities) can be lost when the process exits.
  await tracing?.provider.shutdown();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
