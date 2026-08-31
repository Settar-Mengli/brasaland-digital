import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  envFlagEnabled,
  isTurnstileVerificationEnabled,
  resolveClientIpFromRequest,
  verifyTurnstileToken,
} from './turnstile-verify';

describe('turnstile-verify', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('envFlagEnabled accepts common truthy values', () => {
    process.env.TEST_FLAG = 'true';
    expect(envFlagEnabled('TEST_FLAG')).toBe(true);
    process.env.TEST_FLAG = '1';
    expect(envFlagEnabled('TEST_FLAG')).toBe(true);
    process.env.TEST_FLAG = 'false';
    expect(envFlagEnabled('TEST_FLAG')).toBe(false);
  });

  it('isTurnstileVerificationEnabled reads TURNSTILE_ENABLED', () => {
    process.env.TURNSTILE_ENABLED = 'true';
    expect(isTurnstileVerificationEnabled()).toBe(true);
    process.env.TURNSTILE_ENABLED = 'false';
    expect(isTurnstileVerificationEnabled()).toBe(false);
  });

  it('resolveClientIpFromRequest prefers first x-forwarded-for entry', () => {
    const request = new Request('http://localhost/api/chat', {
      headers: { 'x-forwarded-for': '203.0.113.1, 10.0.0.1' },
    });
    expect(resolveClientIpFromRequest(request)).toBe('203.0.113.1');
  });

  it('resolveClientIpFromRequest falls back to x-real-ip', () => {
    const request = new Request('http://localhost/api/chat', {
      headers: { 'x-real-ip': '198.51.100.2' },
    });
    expect(resolveClientIpFromRequest(request)).toBe('198.51.100.2');
  });

  it('verifyTurnstileToken returns false without secret', async () => {
    delete process.env.TURNSTILE_SECRET_KEY;
    await expect(verifyTurnstileToken('token')).resolves.toBe(false);
  });

  it('verifyTurnstileToken returns true when siteverify succeeds', async () => {
    process.env.TURNSTILE_SECRET_KEY = '1x0000000000000000000000000000000AA';
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ success: true }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(verifyTurnstileToken('dummy-token', '203.0.113.1')).resolves.toBe(true);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calls = fetchMock.mock.calls as unknown as Array<[string, { body: URLSearchParams }]>;
    expect(calls[0][0]).toBe('https://challenges.cloudflare.com/turnstile/v0/siteverify');
    expect(calls[0][1].body.get('secret')).toBe('1x0000000000000000000000000000000AA');
    expect(calls[0][1].body.get('response')).toBe('dummy-token');
    expect(calls[0][1].body.get('remoteip')).toBe('203.0.113.1');
  });

  it('verifyTurnstileToken returns false when siteverify fails', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ success: false }),
      })),
    );

    await expect(verifyTurnstileToken('bad-token')).resolves.toBe(false);
  });

  it('verifyTurnstileToken returns false when siteverify HTTP fails', async () => {
    process.env.TURNSTILE_SECRET_KEY = 'secret';
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: false,
        json: async () => ({}),
      })),
    );

    await expect(verifyTurnstileToken('token')).resolves.toBe(false);
  });
});
