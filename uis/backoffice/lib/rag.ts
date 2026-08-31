import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import { resolveStaffApiBase } from './staff-paths';
import type { KnowledgeQueryResponse } from './rag-types';

function getKnowledgeBaseUrl(): string {
  return resolveStaffApiBase('knowledge', 'NEXT_PUBLIC_KNOWLEDGE_API_URL');
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
