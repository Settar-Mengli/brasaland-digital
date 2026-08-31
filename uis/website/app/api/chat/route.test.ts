import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const verifyTurnstileToken = vi.fn();
const websiteServiceAccessToken = vi.fn();

vi.mock('@/lib/turnstile-verify', () => ({
  envFlagEnabled: (name: string) => {
    const raw = process.env[name]?.trim().toLowerCase();
    return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
  },
  isTurnstileVerificationEnabled: () => {
    const raw = process.env.TURNSTILE_ENABLED?.trim().toLowerCase();
    return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
  },
  resolveClientIpFromRequest: () => '203.0.113.1',
  verifyTurnstileToken: (...args: unknown[]) => verifyTurnstileToken(...args),
}));

vi.mock('@/lib/service-token', () => ({
  websiteServiceAccessToken: (...args: unknown[]) => websiteServiceAccessToken(...args),
}));

import { POST } from './route';

describe('POST /api/chat', () => {
  const originalEnv = { ...process.env };
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    process.env = {
      ...originalEnv,
      NEXT_PUBLIC_PUBLIC_CHAT_ENABLED: 'true',
      PUBLIC_KNOWLEDGE_API_ORIGIN: 'http://knowledge.test',
      TURNSTILE_ENABLED: 'false',
    };
    verifyTurnstileToken.mockReset();
    websiteServiceAccessToken.mockReset();
    websiteServiceAccessToken.mockResolvedValue('service-token');
    fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ answer: 'Test answer' }),
    }));
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('returns 404 when public chat is disabled', async () => {
    process.env.NEXT_PUBLIC_PUBLIC_CHAT_ENABLED = 'false';
    const response = await POST(
      new Request('http://localhost/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question: 'Hours?' }),
      }),
    );
    expect(response.status).toBe(404);
  });

  it('skips Turnstile when disabled and calls knowledge', async () => {
    const response = await POST(
      new Request('http://localhost/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question: 'Hours?' }),
      }),
    );

    expect(response.status).toBe(200);
    expect(verifyTurnstileToken).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith(
      'http://knowledge.test/public/knowledge/query',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('verifies Turnstile and proceeds when enabled with valid token', async () => {
    process.env.TURNSTILE_ENABLED = 'true';
    verifyTurnstileToken.mockResolvedValue(true);

    const response = await POST(
      new Request('http://localhost/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question: 'Hours?', turnstileToken: 'valid-token' }),
      }),
    );

    expect(response.status).toBe(200);
    expect(verifyTurnstileToken).toHaveBeenCalledWith('valid-token', '203.0.113.1');
    expect(fetchMock).toHaveBeenCalled();
  });

  it('returns 403 when Turnstile enabled and token invalid', async () => {
    process.env.TURNSTILE_ENABLED = 'true';
    verifyTurnstileToken.mockResolvedValue(false);

    const response = await POST(
      new Request('http://localhost/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question: 'Hours?', turnstileToken: 'bad-token' }),
      }),
    );

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ detail: 'Turnstile verification failed' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('returns 403 when Turnstile enabled and token missing', async () => {
    process.env.TURNSTILE_ENABLED = 'true';

    const response = await POST(
      new Request('http://localhost/api/chat', {
        method: 'POST',
        body: JSON.stringify({ question: 'Hours?' }),
      }),
    );

    expect(response.status).toBe(403);
    expect(verifyTurnstileToken).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
