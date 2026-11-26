import { describe, expect, it } from 'vitest';
import { APPLICATIONS } from '../src/applications';
import { evaluateBudget, evaluateEligibility } from '../src/activities/rules';
import { buildSummaryMessages, summarize, type ChatClient } from '../src/activities/summary';

const app = APPLICATIONS[1];
const eligibility = evaluateEligibility(app);
const budget = evaluateBudget(app);

describe('reviewer summary', () => {
  it('puts the checks into the prompt', () => {
    const [, user] = buildSummaryMessages(app, eligibility, budget);
    expect(JSON.parse(user.content).budget.budgetTotal).toBe(3600);
  });

  it('runs through the traced wrapper with tracking disabled', async () => {
    process.env.OPIK_TRACK_DISABLE = 'true';
    const stub: ChatClient = {
      chat: async () => ({ content: 'Revise the budget.', model: 'stub', usage: { promptTokens: 1, completionTokens: 1 } }),
    };
    expect(await summarize(stub, app, eligibility, budget)).toBe('Revise the budget.');
  });
});
