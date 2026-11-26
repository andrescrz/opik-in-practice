// One command: temporal dev server -> worker process -> client -> shut everything down.
import '../src/env';
import * as path from 'node:path';
import { spawn, type ChildProcess } from 'node:child_process';
import { reviewAll } from '../src/client';

const PORT = Number(process.env.TEMPORAL_DEV_PORT ?? 7233);
const UI_PORT = Number(process.env.TEMPORAL_DEV_UI_PORT ?? PORT + 1);
const root = path.join(__dirname, '..');

function waitFor(child: ChildProcess, marker: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const onData = (chunk: Buffer) => {
      process.stdout.write(`[worker] ${chunk}`);
      if (chunk.toString().includes(marker)) resolve();
    };
    child.stdout!.on('data', onData);
    child.stderr!.on('data', onData);
    child.on('exit', (code) => reject(new Error(`process exited early with code ${code}`)));
  });
}

async function stop(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null) return;
  child.removeAllListeners('exit');
  const exited = new Promise((resolve) => child.once('exit', resolve));
  child.kill('SIGINT');
  await exited;
}

async function main() {
  const address = `127.0.0.1:${PORT}`;
  const server = spawn(
    'temporal',
    ['server', 'start-dev', '--port', String(PORT), '--ui-port', String(UI_PORT), '--headless', '--log-level', 'error'],
    { stdio: ['ignore', 'pipe', 'pipe'] },
  );
  let worker: ChildProcess | undefined;
  try {
    await waitServer(address);
    worker = spawn(path.join(root, 'node_modules', '.bin', 'tsx'), [path.join(root, 'src', 'worker.ts')], {
      env: { ...process.env, TEMPORAL_ADDRESS: address },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    await waitFor(worker, 'WORKER_READY');
    await reviewAll(address);
  } finally {
    if (worker) await stop(worker);
    await stop(server);
  }
}

async function waitServer(address: string): Promise<void> {
  const { Connection } = await import('@temporalio/client');
  for (let i = 0; i < 60; i++) {
    try {
      const c = await Connection.connect({ address, connectTimeout: 1000 });
      await c.close();
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  throw new Error('Temporal dev server did not start');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
