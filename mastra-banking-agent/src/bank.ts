// The credit union's "core banking system": fictional JSON files loaded into
// memory. Freezing a card mutates this in-memory state only, so every demo run
// starts from the same data.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface Account { account_id: string; type: string; balance_usd: number }
export interface Card { card_id: string; account_id: string; last4: string; status: "active" | "frozen" }
export interface Member { member_id: string; name: string; accounts: Account[]; cards: Card[] }
export interface Transaction { account_id: string; date: string; merchant: string; amount_usd: number }

const readJson = <T>(file: string): T =>
  JSON.parse(readFileSync(fileURLToPath(new URL(`../data/${file}`, import.meta.url)), "utf8")) as T;

const members = readJson<{ members: Member[] }>("members.json").members;
const transactions = readJson<Transaction[]>("transactions.json");

export function findAccount(accountId: string) {
  for (const m of members) {
    const account = m.accounts.find((a) => a.account_id === accountId);
    if (account) return { member: m, account };
  }
  return undefined;
}

export function recentTransactions(accountId: string, limit: number): Transaction[] {
  return transactions
    .filter((t) => t.account_id === accountId)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, limit);
}

export function findCard(cardId: string): Card | undefined {
  return members.flatMap((m) => m.cards).find((c) => c.card_id === cardId);
}

export function memberCards(memberId: string): Card[] {
  return members.find((m) => m.member_id === memberId)?.cards ?? [];
}
