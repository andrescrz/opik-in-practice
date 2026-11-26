import OpenAI from 'openai';
import '../env';
import type { Application, BudgetResult, EligibilityResult } from '../types';

// Never inherit a proxy base URL from the shell; talk to the public OpenAI API.
delete process.env.OPENAI_BASE_URL;

export const MODEL = 'gpt-4o-mini';

export interface ChatClient {
  chat: (messages: { role: 'system' | 'user'; content: string }[]) => Promise<string>;
}

export function openAiChatClient(): ChatClient {
  const openai = new OpenAI();
  return {
    async chat(messages) {
      const response = await openai.chat.completions.create({ model: MODEL, messages });
      return response.choices[0]?.message?.content ?? '';
    },
  };
}

export function buildSummaryMessages(app: Application, eligibility: EligibilityResult, budget: BudgetResult | null) {
  return [
    {
      role: 'system' as const,
      content:
        'You write the reviewer summary for a small neighborhood grant fund. In 3 to 4 plain sentences, ' +
        'describe the project, state whether it meets the fund rules and whether the budget adds up, ' +
        'and end with one recommendation sentence. If budget is null the ledger check was skipped because the application is ineligible. Do not invent facts.',
    },
    {
      role: 'user' as const,
      content: JSON.stringify({
        project: app.projectTitle,
        organization: app.organization,
        description: app.description,
        requestedAmount: app.requestedAmount,
        eligibility,
        budget,
      }),
    },
  ];
}

export async function summarize(
  client: ChatClient,
  app: Application,
  eligibility: EligibilityResult,
  budget: BudgetResult | null,
): Promise<string> {
  return await client.chat(buildSummaryMessages(app, eligibility, budget));
}
