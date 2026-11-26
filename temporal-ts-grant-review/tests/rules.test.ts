import { describe, expect, it } from 'vitest';
import { APPLICATIONS } from '../src/applications';
import { decide, evaluateBudget, evaluateEligibility } from '../src/activities/rules';

const [clean, mismatch, outOfArea] = APPLICATIONS;

describe('eligibility', () => {
  it('accepts an in-area application within the cap', () => {
    expect(evaluateEligibility(clean).eligible).toBe(true);
  });

  it('rejects an application from outside the fund area', () => {
    const result = evaluateEligibility(outOfArea);
    expect(result.eligible).toBe(false);
    expect(result.reasons[0]).toContain('Northgate');
  });
});

describe('budget', () => {
  it('passes when the lines add up to the request', () => {
    expect(evaluateBudget(clean)).toMatchObject({ ok: true, budgetTotal: 3200 });
  });

  it('flags lines that do not add up to the request', () => {
    const result = evaluateBudget(mismatch);
    expect(result.ok).toBe(false);
    expect(result.findings[0]).toContain('$3600');
  });
});

describe('decision', () => {
  it('maps the checks to a verdict', () => {
    expect(decide(evaluateEligibility(clean), evaluateBudget(clean))).toBe('approve');
    expect(decide(evaluateEligibility(mismatch), evaluateBudget(mismatch))).toBe('revise-and-resubmit');
    expect(decide(evaluateEligibility(outOfArea), null)).toBe('decline');
  });
});
