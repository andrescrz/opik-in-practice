import { describe, expect, it } from "vitest";
import { getBalance, getRecentTransactions, freezeCard } from "../src/tools.ts";
import { findCard } from "../src/bank.ts";

// Mastra tools are plain async functions behind createTool, so they run offline.
// With no Opik exporter configured (the case here: nothing imports src/mastra.ts),
// nothing is traced and nothing hits the network.
const run = (tool: any, input: unknown) => tool.execute(input, {});

describe("banking tools", () => {
  it("returns a balance and the member's cards", async () => {
    const out = await run(getBalance, { account_id: "CHK-2041-01" });
    expect(out.balance_usd).toBe(2418.37);
    expect(out.cards[0].card_id).toBe("CARD-7731");
  });

  it("returns an error object for an unknown account", async () => {
    expect(await run(getBalance, { account_id: "NOPE" })).toEqual({ error: "No account NOPE" });
  });

  it("lists transactions newest first and honours the limit", async () => {
    const out = await run(getRecentTransactions, { account_id: "CHK-2041-01", limit: 3 });
    expect(out.transactions).toHaveLength(3);
    expect(out.transactions[0].date >= out.transactions[2].date).toBe(true);
  });

  it("freezes a card in memory", async () => {
    expect(findCard("CARD-4402")?.status).toBe("active");
    const out = await run(freezeCard, { card_id: "CARD-4402" });
    expect(out).toEqual({ card_id: "CARD-4402", last4: "4402", status: "frozen" });
    expect(findCard("CARD-4402")?.status).toBe("frozen");
  });
});
