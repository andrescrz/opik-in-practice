import { proxyActivities } from '@temporalio/workflow';
import type * as activities from '../activities';
import type { Application, ReviewOutcome } from '../types';

const { checkEligibility, checkBudget, writeReviewerSummary, recordDecision } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 minute',
  retry: { initialInterval: '1 second', backoffCoefficient: 1.5, maximumAttempts: 5 },
});

export async function reviewApplication(app: Application): Promise<ReviewOutcome> {
  const eligibility = await checkEligibility(app);
  // Ineligible applications skip the ledger check but still get a written summary.
  const budget = eligibility.eligible ? await checkBudget(app) : null;
  const summary = await writeReviewerSummary(app, eligibility, budget);
  return await recordDecision(app, eligibility, budget, summary);
}
