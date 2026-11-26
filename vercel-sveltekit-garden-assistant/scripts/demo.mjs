// Starts the SvelteKit dev server, plays scripted multi-turn conversations against
// /api/chat (streaming), prints the replies, then shuts the server down.
import { spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
import { randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
for (let dir = root; ; dir = path.dirname(dir)) {
  if (existsSync(path.join(dir, ".env"))) {
    config({ path: path.join(dir, ".env"), quiet: true });
    break;
  }
  if (dir === path.dirname(dir)) break;
}

const PORT = process.env.DEMO_PORT || "4173";
const BASE = `http://localhost:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const conversations = [
  {
    title: "Tomatoes and blight",
    turns: [
      "When can I plant out my tomatoes in Fernwick Vale, and how deep should I set them?",
      "Some leaves have brown patches with a yellow halo. What is it and what do I do?",
      "How often should I water them once they are in?",
    ],
  },
  {
    title: "Aphids on the beans",
    turns: [
      "There are tiny green insects clustered on my bean shoots and the leaves are sticky. What are they?",
      "Is there a way to get rid of them without spraying anything harsh?",
    ],
  },
  {
    title: "Basil and the cold",
    turns: [
      "Can I sow basil outdoors in early May?",
      "What is the best way to water basil in pots?",
    ],
  },
];

console.log(`Starting SvelteKit dev server on port ${PORT}...`);
const server = spawn(
  path.join(root, "node_modules", ".bin", "vite"),
  ["dev", "--port", PORT, "--strictPort"],
  { cwd: root, env: { ...process.env }, stdio: ["ignore", "pipe", "pipe"], detached: true },
);
server.stdout.on("data", () => {});
server.stderr.on("data", (d) => {
  const line = d.toString();
  if (/error/i.test(line)) process.stderr.write(line);
});

async function waitForServer(timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(BASE, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return;
    } catch {
      /* not up yet */
    }
    await sleep(500);
  }
  throw new Error("Dev server did not become ready in time");
}

// POSTs the full history (what the Chat class does) and reads the UI-message SSE stream.
async function chatTurn(chatId, messages) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: chatId, messages }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

  let text = "";
  let buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) {
          text += event.delta;
          process.stdout.write(event.delta);
        }
      } catch {
        /* ignore non-JSON keepalives */
      }
    }
  }
  process.stdout.write("\n");
  return text;
}

const message = (role, text) => ({ id: randomUUID(), role, parts: [{ type: "text", text }] });

try {
  await waitForServer();
  console.log("Server is ready.\n");

  for (const conversation of conversations) {
    const chatId = randomUUID();
    console.log(`=== ${conversation.title} (chat ${chatId.slice(0, 8)}) ===`);
    const history = [];
    for (const turn of conversation.turns) {
      console.log(`\nYou: ${turn}\nSprout: `);
      history.push(message("user", turn));
      history.push(message("assistant", await chatTurn(chatId, history)));
    }
    console.log();
  }
  console.log("Done.");
} finally {
  try {
    process.kill(-server.pid, "SIGTERM");
  } catch {
    /* already gone */
  }
}
