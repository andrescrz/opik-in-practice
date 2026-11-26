import { config } from "dotenv";
import { existsSync } from "node:fs";
import path from "node:path";

// Walk up from the app folder to the first .env so a repo-root .env works too.
// dotenv never overrides variables that are already exported in the shell.
let dir = process.cwd();
for (;;) {
  const candidate = path.join(dir, ".env");
  if (existsSync(candidate)) {
    config({ path: candidate, quiet: true });
    break;
  }
  const parent = path.dirname(dir);
  if (parent === dir) break;
  dir = parent;
}
