import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages, type UIMessage } from "ai";
import { OpikExporter } from "opik-vercel";
import type { RequestHandler } from "./$types";
import { buildSystemPrompt, loadNotes, retrieve } from "$lib/server/notes";

const notes = loadNotes();

function userText(message: UIMessage): string {
  return message.parts.map((part) => (part.type === "text" ? part.text : "")).join(" ");
}

export const POST: RequestHandler = async ({ request }) => {
  const { id, messages }: { id: string; messages: UIMessage[] } = await request.json();

  // Retrieve on the last two user messages so a follow-up like "and how often should I water it?" still finds the right note.
  const query = messages
    .filter((m) => m.role === "user")
    .slice(-2)
    .map(userText)
    .join(" ");

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: buildSystemPrompt(retrieve(query, notes)),
    messages: await convertToModelMessages(messages),

    // The chat id and trace name ride in runtimeContext and become the Opik thread id and trace name
    // (see telemetry.ts). Without includeRuntimeContext the spans carry neither.
    runtimeContext: { threadId: id, traceName: "garden-chat-turn" },
    experimental_telemetry: {
      ...OpikExporter.getSettings({ name: "garden-chat-turn" }),
      includeRuntimeContext: { threadId: true, traceName: true },
    },
  });

  return result.toUIMessageStreamResponse();
};
