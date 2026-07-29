import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import type { KnowledgeQueryResponse } from './rag-types';

/**
 * Same-origin knowledge API base (rewritten to KNOWLEDGE_API_ORIGIN).
 */
function getKnowledgeBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_KNOWLEDGE_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_KNOWLEDGE_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

function requireAccessToken(): string {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  return token;
}

/**
 * Ask the knowledge base a question. Requires a Bearer JWT (metered LLM gateway).
 */
export async function askKnowledge(question: string): Promise<string> {
  const token = requireAccessToken();
  const response = await fetch(`${getKnowledgeBaseUrl()}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  const data = (await response.json()) as KnowledgeQueryResponse;
  return data.answer;
}
