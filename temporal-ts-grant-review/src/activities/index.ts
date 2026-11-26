import { activityInfo } from '@temporalio/activity';
import type { Application, BudgetResult, EligibilityResult, ReviewOutcome, Verdict } from '../types';
import { decide, evaluateBudget, evaluateEligibility } from './rules';
import { openAiChatClient, summarize } from './summary';

export async function checkEligibility(app: Application): Promise<EligibilityResult> {
  return evaluateEligibility(app);
}

export async function checkBudget(app: Application): Promise<BudgetResult> {
  // Simulated flaky ledger service: the first attempt always fails, and the
  // retry policy in the workflow makes the second one succeed.
  if (activityInfo().attempt === 1) {
    throw new Error('Ledger service unavailable: connection reset (transient, succeeds on retry)');
  }
  return evaluateBudget(app);
}

export async function writeReviewerSummary(
  app: Application,
  eligibility: EligibilityResult,
  budget: BudgetResult | null,
): Promise<string> {
  return await summarize(openAiChatClient(), app, eligibility, budget);
}

export async function recordDecision(
  app: Application,
  eligibility: EligibilityResult,
  budget: BudgetResult | null,
  summary: string,
): Promise<ReviewOutcome> {
  const verdict: Verdict = decide(eligibility, budget);
  return { applicationId: app.id, eligibility, budget, summary, verdict };
}
