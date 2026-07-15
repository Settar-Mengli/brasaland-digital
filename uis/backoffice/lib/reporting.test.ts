import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const REPORTING_BASE = 'http://localhost:3003/api/reporting';

describe('reporting client', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_REPORTING_API_URL', REPORTING_BASE);
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

    expect(fetchMock).toHaveBeenCalledWith(
      `${REPORTING_BASE}/weekly-location-performance?week_start=2026-07-06`,
      undefined,
    );
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
