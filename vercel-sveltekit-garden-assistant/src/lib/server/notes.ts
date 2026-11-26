import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

export interface Note {
  name: string;
  text: string;
}

const STOPWORDS = new Set([
  "the", "and", "for", "with", "that", "this", "what", "when", "how", "should",
  "does", "are", "you", "your", "can", "about", "from", "into", "have", "has",
  "its", "they", "them", "there", "then", "than", "any", "but", "not", "too",
]);

export function loadNotes(dir = path.join(process.cwd(), "data")): Note[] {
  return readdirSync(dir)
    .filter((file) => file.endsWith(".md"))
    .sort()
    .map((file) => ({
      name: file.replace(/\.md$/, ""),
      text: readFileSync(path.join(dir, file), "utf8").trim(),
    }));
}

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z]{3,}/g) ?? [])
    .filter((word) => !STOPWORDS.has(word))
    .map((word) => word.replace(/(ies|es|s)$/, ""));
}

// Keyword overlap is plenty for six short notes; it keeps the example free of an embeddings dependency.
export function retrieve(query: string, notes: Note[], k = 2): Note[] {
  const queryTerms = new Set(tokenize(query));
  return notes
    .map((note) => {
      const noteTerms = new Set(tokenize(note.text));
      let score = 0;
      for (const term of queryTerms) if (noteTerms.has(term)) score += 1;
      return { note, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((entry) => entry.note);
}

export function buildSystemPrompt(retrieved: Note[]): string {
  const context = retrieved.length
    ? retrieved.map((note) => `## ${note.name}\n${note.text}`).join("\n\n")
    : "(no matching notes)";
  return `You are Sprout, the garden helper for the Fernwick Vale community plot, a fictional
cool-temperate valley garden. You help with planting calendars, pest identification and watering.
Answer in two to four sentences, using the plot notes below when they apply. If the notes do not
cover the question, say so plainly and give only general advice you are confident about.

Plot notes:
${context}`;
}
