import { ReActAgent } from "beeai-framework/agents/react/agent";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { MODEL } from "./config.ts";
import { tools } from "./tools.ts";

export const INSTRUCTIONS = `You triage animal-care requests for keepers at Marrow Creek Zoo.

For each request:
1. Look up the animal's care record to learn what is normal for it. Use its enclosure id for the next step.
2. Check the enclosure's maintenance log. An open item may explain, or cause, what the keeper is seeing.
3. Decide the urgency: "emergency" (animal in danger or an alarm affecting life support), "same-day", or "routine".
4. Look up the roster and name who to call: the care area for animal behaviour, aquatics for life-support or pool equipment alarms, facilities for other enclosure repairs.
Never name a person, number or enclosure fact you did not get from a tool.

Final answer format:
Urgency: <emergency | same-day | routine>
Call: <name> (<contact>)
Why: <2-3 sentences citing the care record and any open maintenance item>
First steps for the keeper: <1-3 short actions>`;

export const DEFAULT_LIMITS = { maxRetriesPerStep: 3, totalMaxRetries: 10, maxIterations: 8 };

export async function triage(request: string, limits = DEFAULT_LIMITS): Promise<string> {
  // A fresh agent and memory per request keeps every request an independent run.
  const agent = new ReActAgent({
    llm: new OpenAIChatModel(MODEL),
    tools,
    memory: new UnconstrainedMemory(),
  });
  const response = await agent.run({ prompt: `${INSTRUCTIONS}\n\nKeeper report: "${request}"` }, { execution: limits });
  return response.result.text;
}
