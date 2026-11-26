import * as fs from 'node:fs';
import * as path from 'node:path';
import * as dotenv from 'dotenv';

// Walk up from the example folder and load the first .env found. dotenv never
// overrides variables that are already exported, so the shell wins.
function findEnvFile(): string | undefined {
  let dir = path.resolve(__dirname, '..');
  for (;;) {
    const candidate = path.join(dir, '.env');
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) return undefined;
    dir = parent;
  }
}

const envFile = findEnvFile();
if (envFile) dotenv.config({ path: envFile, quiet: true });

export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}
