import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const REPORTING_BASE = 'http://localhost:3003/api/reporting';

describe('reporting client', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_REPORTING_API_URL', REPORTING_BASE);
    vi.stubGlobal('window', globalThis);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'reporting-admin-token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    });
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('getWeeklyLocationPerformance calls base URL and appends week_start query', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          week_start: '2026-07-06',
          locations: [],
        }),
        { status: 200 },
      ),
    );

    const { getWeeklyLocationPerformance } = await import('./reporting');
    await getWeeklyLocationPerformance('2026-07-06');

    const [url, init] = fetchMock.mock.calls[0] ?? [];
    expect(url).toBe(`${REPORTING_BASE}/weekly-location-performance?week_start=2026-07-06`);
    expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer reporting-admin-token');
  });

  it('getWeeklyLocationPerformance surfaces parseApiError on failure', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'reporting unavailable' }), {
        status: 503,
        statusText: 'Service Unavailable',
      }),
    );

    const { getWeeklyLocationPerformance } = await import('./reporting');

    await expect(getWeeklyLocationPerformance()).rejects.toThrow('reporting unavailable');
  });
});
