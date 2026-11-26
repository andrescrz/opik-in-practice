import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { getBalance, getRecentTransactions, freezeCard } from "./tools.ts";

export const bankingAgent = new Agent({
  id: "banking-agent",
  name: "harbor-pines-assistant",
  instructions:
    "You are the virtual assistant of Harbor Pines Credit Union. Ground every answer in tool " +
    "results; never guess balances or transactions. Call get_balance before quoting a balance " +
    "(it also lists the member's cards) and get_recent_transactions before discussing activity. " +
    "Only call freeze_card when the member clearly asks for it, using a card id you got from a tool. " +
    "Be calm and concise: 2-4 sentences, no bullet lists.",
  model: openai("gpt-4o-mini"),
  tools: { getBalance, getRecentTransactions, freezeCard },
});
