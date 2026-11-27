// Offline checks on the exported workflow: no n8n, no Opik, no keys. Run: node --test
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const load = (path) => JSON.parse(readFileSync(new URL(`../${path}`, import.meta.url), "utf8"));
const workflow = load("workflow/volunteer-screening.json");
const signups = load("data/signups.json");
const node = (name) => workflow.nodes.find((n) => n.name === name);
const next = (name, output = 0) => workflow.connections[name].main[output].map((c) => c.node);

// Runs the Code node's JavaScript the way n8n does for "Run Once for All Items".
function checkShiftRules(signup) {
  const run = new Function("$input", node("Check shift rules").parameters.jsCode);
  return run({ first: () => ({ json: { body: signup } }) })[0].json.hard_blockers;
}

test("the workflow has no tracing nodes; the hook does all of it", () => {
  for (const n of workflow.nodes) assert.doesNotMatch(n.type, /opik|otel|telemetry/i, n.name);
});

test("the nodes are chained as the README's span tree describes", () => {
  assert.deepEqual(next("Sign-up form"), ["Check shift rules"]);
  assert.deepEqual(next("Check shift rules"), ["Screen motivation (gpt-4o-mini)"]);
  assert.deepEqual(next("Screen motivation (gpt-4o-mini)"), ["Needs a coordinator?"]);
  assert.deepEqual(next("Needs a coordinator?", 0), ["Queue for coordinator"]);
  assert.deepEqual(next("Needs a coordinator?", 1), ["Ready to schedule"]);
  assert.deepEqual(next("Queue for coordinator"), ["Reply to form"]);
  assert.deepEqual(next("Ready to schedule"), ["Reply to form"]);
});

test("the webhook path matches what demo.sh posts to", () => {
  assert.equal(node("Sign-up form").parameters.path, "volunteer-signup");
  assert.match(readFileSync(new URL("../demo.sh", import.meta.url), "utf8"), /\/webhook\/volunteer-signup/);
});

test("shift rules on the demo sign-ups", () => {
  const blockers = Object.fromEntries(signups.map((s) => [s.name, checkShiftRules(s)]));
  assert.deepEqual(blockers, {
    "Priya Raman": [],
    "Jonah Whitaker": ["must be 21+ for delivery_driver"],
    "Carmen Delgado": [],
    "Ollie Brandt": [],
  });
});

test("shift rules flag missing certificates and unknown roles", () => {
  assert.deepEqual(
    checkShiftRules({ age: 30, preferred_role: "kids_snack_program", certifications: [] }),
    ["missing background_check"],
  );
  assert.deepEqual(
    checkShiftRules({ age: 30, preferred_role: "forklift", certifications: [] }),
    ['unknown role "forklift"'],
  );
});
