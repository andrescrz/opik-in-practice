import './env';
import { NativeConnection, Worker } from '@temporalio/worker';
import * as activities from './activities';
import { TASK_QUEUE } from './types';

async function main() {
  const address = process.env.TEMPORAL_ADDRESS ?? 'localhost:7233';
  const connection = await NativeConnection.connect({ address });
  const worker = await Worker.create({
    connection,
    taskQueue: TASK_QUEUE,
    workflowsPath: require.resolve('./workflows'),
    activities,
  });
  console.log(`WORKER_READY on ${address}, task queue "${TASK_QUEUE}"`);
  await worker.run();
  await connection.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
