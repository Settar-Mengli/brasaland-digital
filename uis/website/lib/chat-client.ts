import type { GuestChatErrorBody, GuestChatResponse } from './chat-types';

export async function askGuestChat(question: string, turnstileToken?: string): Promise<string> {
  const body: { question: string; turnstileToken?: string } = { question };
  if (turnstileToken) {
    body.turnstileToken = turnstileToken;
  }

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = 'Unable to get an answer right now.';
    try {
      const body = (await response.json()) as GuestChatErrorBody;
      if (body.detail?.trim()) {
        detail = body.detail.trim();
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  const data = (await response.json()) as GuestChatResponse;
  return data.answer;
}
