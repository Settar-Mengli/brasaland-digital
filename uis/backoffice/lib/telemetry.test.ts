import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { shouldEmitSessionExpired } from './telemetry';

const TELEMETRY_ENDPOINT = 'http://localhost:3003/api/telemetry/events';
const TOKEN_KEY = 'brasaland_access_token';

function makeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.signature`;
}

function createStorage(): Storage {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
}

describe('telemetry service', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_TELEMETRY_ENDPOINT', TELEMETRY_ENDPOINT);
    vi.stubGlobal('window', globalThis);
    vi.stubGlobal('crypto', {
      randomUUID: vi.fn(() => 'test-uuid'),
    });
    vi.stubGlobal('localStorage', createStorage());
    vi.stubGlobal('sessionStorage', createStorage());
    vi.stubGlobal('fetch', vi.fn());
    vi.stubGlobal('navigator', { sendBeacon: vi.fn(() => true) });
    vi.stubGlobal('document', {
      hidden: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-07-09T08:00:00.000Z'));
  });

  afterEach(async () => {
    const { __resetTelemetryForTests } = await import('./telemetry');
    __resetTelemetryForTests();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('builds the full envelope with mocked sources', async () => {
    localStorage.setItem(TOKEN_KEY, makeJwt({ sub: '42' }));
    sessionStorage.setItem('brasaland_telemetry_session_id', 'session-1');

    const { track, __getQueueForTests } = await import('./telemetry');
    track('ingredient_list_viewed', { location_id: 'medellin_centro', item_count: 3 });

    const [event] = __getQueueForTests();
    expect(event).toEqual({
      eventId: 'test-uuid',
      timestamp: '2026-07-09T08:00:00.000Z',
      sessionId: 'session-1',
      userId: '42',
      event_type: 'ingredient_list_viewed',
      schemaVersion: '2.0.0',
      requestId: 'test-uuid',
      service: 'backoffice',
      properties: { location_id: 'medellin_centro', item_count: 3 },
    });
  });

  it('does not inject envelope fields into properties', async () => {
    const { track, __getQueueForTests } = await import('./telemetry');
    track('session_expired', { idle_duration_ms: 0, source: 'backoffice' });

    const [event] = __getQueueForTests();
    expect(Object.keys(event.properties)).toEqual(['idle_duration_ms', 'source']);
  });

  it('flushes when the queue reaches 20 events', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }));

    const { track, __getQueueForTests } = await import('./telemetry');
    for (let index = 0; index < 20; index += 1) {
      track('session_expired', { idle_duration_ms: index, source: 'backoffice' });
    }

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    expect(__getQueueForTests()).toHaveLength(0);
  });

  it('flushes on the 10 second interval', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }));

    const { track } = await import('./telemetry');
    track('session_expired', { idle_duration_ms: 0, source: 'backoffice' });

    await vi.advanceTimersByTimeAsync(10_000);

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('retries fetch flush three times then discards the batch', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockRejectedValue(new Error('network error'));

    const { track, __flushQueueForTests, __getQueueForTests } = await import('./telemetry');
    track('session_expired', { idle_duration_ms: 0, source: 'backoffice' });

    const flushPromise = __flushQueueForTests();
    await vi.advanceTimersByTimeAsync(7_000);
    await flushPromise;

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(__getQueueForTests()).toHaveLength(0);
  });

  it('aggregates login failures within the burst window', async () => {
    const { track, __getQueueForTests } = await import('./telemetry');

    track('user_login_failed', { failure_reason: 'wrong_credentials', source: 'backoffice' });
    track('user_login_failed', { failure_reason: 'wrong_credentials', source: 'backoffice' });

    const queue = __getQueueForTests();
    expect(queue).toHaveLength(1);
    expect(queue[0].properties).toEqual({
      failure_reason: 'wrong_credentials',
      source: 'backoffice',
      attempt_count: 2,
    });
  });

  it('sendBeacon uses a JSON Blob with application/json type', async () => {
    const sendBeacon = vi.fn(() => true);
    vi.stubGlobal('navigator', { sendBeacon });

    const { track, __beaconQueueForTests } = await import('./telemetry');
    track('session_expired', { idle_duration_ms: 0, source: 'backoffice' });
    __beaconQueueForTests();

    expect(sendBeacon).toHaveBeenCalledTimes(1);
    const [endpoint, payload] = sendBeacon.mock.calls[0] as [string, Blob];
    expect(endpoint).toBe(TELEMETRY_ENDPOINT);
    expect(payload).toBeInstanceOf(Blob);
    expect(payload.type).toBe('application/json');
    const body = JSON.parse(await payload.text()) as {
      events: Array<{ event_type: string; properties: Record<string, unknown> }>;
    };
    expect(body.events).toHaveLength(1);
    expect(body.events[0].event_type).toBe('session_expired');
    expect(body.events[0].properties).toEqual({ idle_duration_ms: 0, source: 'backoffice' });
  });
});

describe('shouldEmitSessionExpired', () => {
  it('returns false for a plain unauthenticated visit with no session evidence', () => {
    expect(
      shouldEmitSessionExpired({
        token: null,
        tokenExpired: false,
        hasSessionEvidence: false,
      }),
    ).toBe(false);
  });

  it('returns true when telemetry session keys exist but the token is missing', () => {
    expect(
      shouldEmitSessionExpired({
        token: null,
        tokenExpired: false,
        hasSessionEvidence: true,
      }),
    ).toBe(true);
  });

  it('returns true when a token exists but is expired', () => {
    expect(
      shouldEmitSessionExpired({
        token: 'jwt-token',
        tokenExpired: true,
        hasSessionEvidence: false,
      }),
    ).toBe(true);
  });

  it('returns false when a valid token is present', () => {
    expect(
      shouldEmitSessionExpired({
        token: 'jwt-token',
        tokenExpired: false,
        hasSessionEvidence: true,
      }),
    ).toBe(false);
  });
});
