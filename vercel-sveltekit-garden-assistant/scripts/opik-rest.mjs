// Small REST helpers for the parts of Opik the SDK does not wrap: the project and its online-evaluation rule.
export const PROJECT = process.env.OPIK_PROJECT_NAME || "vercel-sveltekit-garden-assistant";
export const RULE_NAME = "answer_relevance";

const base = (process.env.OPIK_URL_OVERRIDE || "http://localhost:5173/api/").replace(/\/?$/, "/");
const headers = {
  "Content-Type": "application/json",
  "Comet-Workspace": process.env.OPIK_WORKSPACE || "default",
  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
};

async function api(method, route, body) {
  const res = await fetch(base + route, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(`${method} ${route} -> ${res.status}: ${await res.text()}`);
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

async function ensureProject() {
  const found = await api("GET", `v1/private/projects?name=${encodeURIComponent(PROJECT)}&size=100`);
  const hit = found.content.find((p) => p.name === PROJECT);
  if (hit) return hit.id;
  await api("POST", "v1/private/projects", { name: PROJECT });
  return (await api("GET", `v1/private/projects?name=${encodeURIComponent(PROJECT)}&size=100`)).content.find(
    (p) => p.name === PROJECT,
  ).id;
}

// Creates the online-evaluation rule if it is missing and removes accidental duplicates, so any number of
// runs leaves exactly one rule. The rule must exist before traces arrive: Opik only scores traces ingested
// after the rule is enabled.
export async function ensureRule() {
  const projectId = await ensureProject();
  const list = await api("GET", `v1/private/automations/evaluators?project_id=${projectId}&size=100`);
  const mine = list.content.filter((r) => r.name === RULE_NAME);
  for (const extra of mine.slice(1)) {
    await api("POST", "v1/private/automations/evaluators/delete", { ids: [extra.id] });
  }
  if (mine.length) return { id: mine[0].id, created: false };

  await api("POST", "v1/private/automations/evaluators", {
    name: RULE_NAME,
    type: "llm_as_judge",
    action: "evaluator",
    project_ids: [projectId],
    sampling_rate: 1,
    enabled: true,
    trigger_scope: "production",
    code: {
      model: { name: "gpt-4o-mini", temperature: 0 },
      messages: [
        {
          role: "USER",
          content:
            "You are grading a garden chat assistant.\n\n" +
            "INPUT is the full request the model received: a system prompt with plot notes, then the conversation. " +
            "The gardener's question is the last user message.\n" +
            "OUTPUT is the assistant's reply.\n\n" +
            "Return true if the reply directly addresses the gardener's last question, and false if it is off-topic or " +
            "ignores the question. Do not penalise a reply for saying the notes do not cover something.\n\n" +
            "INPUT:\n{{input}}\n\nOUTPUT:\n{{output}}",
        },
      ],
      variables: { input: "input", output: "output" },
      schema: [
        { name: RULE_NAME, type: "BOOLEAN", description: "True if the reply answers the gardener's question" },
      ],
    },
  });
  const after = await api("GET", `v1/private/automations/evaluators?project_id=${projectId}&size=100`);
  return { id: after.content.find((r) => r.name === RULE_NAME).id, created: true };
}

export async function listTraces() {
  const res = await api("GET", `v1/private/traces?project_name=${encodeURIComponent(PROJECT)}&size=100&truncate=false`);
  return res.content;
}

export async function deleteTraces(ids) {
  if (ids.length) await api("POST", "v1/private/traces/delete", { ids });
}
