export const TASK_QUEUE = 'grant-review';

export interface BudgetLine {
  item: string;
  cost: number;
}

export interface Application {
  id: string;
  applicant: string;
  organization: string;
  neighborhood: string;
  projectTitle: string;
  description: string;
  residentsServed: number;
  requestedAmount: number;
  budget: BudgetLine[];
}

export interface EligibilityResult {
  eligible: boolean;
  reasons: string[];
}

export interface BudgetResult {
  ok: boolean;
  budgetTotal: number;
  findings: string[];
}

export type Verdict = 'approve' | 'revise-and-resubmit' | 'decline';

export interface ReviewOutcome {
  applicationId: string;
  eligibility: EligibilityResult;
  budget: BudgetResult | null;
  summary: string;
  verdict: Verdict;
}
