import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { findAccount, recentTransactions, findCard, memberCards } from "./bank.ts";

export const getBalance = createTool({
  id: "get_balance",
  description: "Get the current balance of a member's account, and the cards attached to that member.",
  inputSchema: z.object({ account_id: z.string().describe("Account id such as CHK-2041-01") }),
  execute: async ({ account_id }) => {
    const hit = findAccount(account_id);
    if (!hit) return { error: `No account ${account_id}` };
    return {
      account_id,
      type: hit.account.type,
      balance_usd: hit.account.balance_usd,
      cards: memberCards(hit.member.member_id),
    };
  },
});

export const getRecentTransactions = createTool({
  id: "get_recent_transactions",
  description: "List the most recent transactions on an account, newest first.",
  inputSchema: z.object({
    account_id: z.string(),
    limit: z.number().int().min(1).max(10).default(5),
  }),
  execute: async ({ account_id, limit }) => {
    if (!findAccount(account_id)) return { error: `No account ${account_id}` };
    return { account_id, transactions: recentTransactions(account_id, limit) };
  },
});

export const freezeCard = createTool({
  id: "freeze_card",
  description: "Freeze a debit card so it cannot be used. Only call after the member has asked for the freeze.",
  inputSchema: z.object({ card_id: z.string().describe("Card id such as CARD-7731") }),
  execute: async ({ card_id }) => {
    const card = findCard(card_id);
    if (!card) return { error: `No card ${card_id}` };
    card.status = "frozen";
    return { card_id, last4: card.last4, status: card.status };
  },
});
