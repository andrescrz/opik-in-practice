import type { Application, BudgetResult, EligibilityResult, Verdict } from '../types';

export const FUND_NEIGHBORHOODS = ['Alderbrook', 'Marsh Hollow', 'Kestrel Park'];
export const MAX_GRANT = 5000;
export const MIN_RESIDENTS = 25;

export function evaluateEligibility(app: Application): EligibilityResult {
  const reasons: string[] = [];
  if (!FUND_NEIGHBORHOODS.includes(app.neighborhood)) {
    reasons.push(`${app.neighborhood} is outside the fund area (${FUND_NEIGHBORHOODS.join(', ')})`);
  }
  if (app.requestedAmount > MAX_GRANT) reasons.push(`request exceeds the $${MAX_GRANT} cap`);
  if (app.residentsServed < MIN_RESIDENTS) reasons.push(`serves fewer than ${MIN_RESIDENTS} residents`);
  return { eligible: reasons.length === 0, reasons };
}

export function evaluateBudget(app: Application): BudgetResult {
  const budgetTotal = app.budget.reduce((sum, line) => sum + line.cost, 0);
  const findings: string[] = [];
  if (budgetTotal !== app.requestedAmount) {
    findings.push(`budget lines add up to $${budgetTotal} but $${app.requestedAmount} was requested`);
  }
  for (const line of app.budget) {
    if (line.cost > app.requestedAmount * 0.6) findings.push(`"${line.item}" is over 60% of the request`);
  }
  return { ok: findings.length === 0, budgetTotal, findings };
}

export function decide(eligibility: EligibilityResult, budget: BudgetResult | null): Verdict {
  if (!eligibility.eligible) return 'decline';
  return budget?.ok ? 'approve' : 'revise-and-resubmit';
}
