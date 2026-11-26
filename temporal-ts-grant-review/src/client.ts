import './env';
import { Client, Connection } from '@temporalio/client';
import { APPLICATIONS } from './applications';
import { TASK_QUEUE } from './types';
import type { reviewApplication } from './workflows';

export async function reviewAll(address: string): Promise<void> {
  const connection = await Connection.connect({ address });
  const client = new Client({ connection });
  for (const app of APPLICATIONS) {
    console.log(`\n=== ${app.id}: ${app.projectTitle}`);
    const handle = await client.workflow.start<typeof reviewApplication>('reviewApplication', {
      taskQueue: TASK_QUEUE,
      workflowId: `review-${app.id}`,
      args: [app],
    });
    const outcome = await handle.result();
    console.log(`Verdict: ${outcome.verdict}`);
    console.log(`Summary: ${outcome.summary}`);
  }
  await connection.close();
}

if (require.main === module) {
  reviewAll(process.env.TEMPORAL_ADDRESS ?? 'localhost:7233').catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
