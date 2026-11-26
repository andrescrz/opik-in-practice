import { existsSync } from "node:fs";
import path from "node:path";
import dotenv from "dotenv";

// Load the nearest .env, walking up from the example folder to the repo root.
export function loadNearestEnv(start: string): void {
  for (let dir = start; ; dir = path.dirname(dir)) {
    const file = path.join(dir, ".env");
    if (existsSync(file)) return void dotenv.config({ path: file });
    if (path.dirname(dir) === dir) return;
  }
}
