import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ["tests/**/*.test.ts"],
    // opik-vercel builds its Opik client at import time, and with no URL it targets Opik
    // Cloud and throws "OPIK_API_KEY is not set". Tests never send anything
    // (OPIK_TRACK_DISABLE), so a local URL is enough to keep them offline.
    env: { OPIK_URL_OVERRIDE: process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api" },
  },
});
