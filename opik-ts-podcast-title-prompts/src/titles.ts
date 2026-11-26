import type OpenAI from "openai";
import type { Episode } from "./episodes.js";

export const MODEL = "gpt-4o-mini";

export function episodeMessage(ep: Episode): string {
  return `Show: ${ep.show}\nEpisode notes: ${ep.notes}`;
}

// Models sometimes wrap the title in quotes or end it with a newline; the
// rules are judged on what the model actually returned, so only trim whitespace.
export function cleanTitle(raw: string | null | undefined): string {
  return (raw ?? "").trim();
}

export async function writeTitle(
  openai: Pick<OpenAI, "chat">,
  systemPrompt: string,
  ep: Episode,
): Promise<string> {
  const res = await openai.chat.completions.create({
    model: MODEL,
    temperature: 0,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: episodeMessage(ep) },
    ],
  });
  return cleanTitle(res.choices[0]?.message.content);
}
