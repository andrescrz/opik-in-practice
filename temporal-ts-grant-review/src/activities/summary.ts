import { SpanStatusCode, trace } from '@opentelemetry/api';
import OpenAI from 'openai';
import '../env';
import type { Application, BudgetResult, EligibilityResult } from '../types';

// Never inherit a proxy base URL from the shell; talk to the public OpenAI API.
delete process.env.OPENAI_BASE_URL;

export const MODEL = 'gpt-4o-mini';

type Message = { role: 'system' | 'user'; content: string };

export interface ChatResult {
  content: string;
  model: string;
  usage?: { promptTokens: number; completionTokens: number };
}

export interface ChatClient {
  chat: (messages: Message[]) => Promise<ChatResult>;
}

export function openAiChatClient(): ChatClient {
  const openai = new OpenAI();
  return {
    async chat(messages) {
      const response = await openai.chat.completions.create({ model: MODEL, messages });
      return {
        content: response.choices[0]?.message?.content ?? '',
        model: response.model,
        usage: response.usage
          ? { promptTokens: response.usage.prompt_tokens, completionTokens: response.usage.completion_tokens }
          : undefined,
      };
    },
  };
}

const tracer = trace.getTracer('grant-activities');

/**
 * Wrap one chat call in a child span of the current RunActivity span. The gen_ai.* attributes
 * are what Opik reads to label the span as an LLM call and to compute token usage and cost;
 * without them the model call would be an anonymous general span with no cost.
 * With no tracer registered (OPIK_TRACK_DISABLE=true) this is a plain pass-through.
 */
export async function tracedChat(client: ChatClient, name: string, messages: Message[]): Promise<string> {
  return await tracer.startActiveSpan(name, async (span) => {
    try {
      const result = await client.chat(messages);
      span.setAttributes({
        'openinference.span.kind': 'LLM',
        'gen_ai.operation.name': 'chat',
        'gen_ai.system': 'openai',
        'gen_ai.request.model': MODEL,
        'gen_ai.response.model': result.model,
        'input.value': JSON.stringify({ messages }),
        'input.mime_type': 'application/json',
        'output.value': result.content,
        'output.mime_type': 'text/plain',
        ...(result.usage
          ? {
              'gen_ai.usage.input_tokens': result.usage.promptTokens,
              'gen_ai.usage.output_tokens': result.usage.completionTokens,
            }
          : {}),
      });
      span.setStatus({ code: SpanStatusCode.OK });
      return result.content;
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
      throw err;
    } finally {
      span.end();
    }
  });
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
  return await tracedChat(client, 'reviewer-summary', buildSummaryMessages(app, eligibility, budget));
}
