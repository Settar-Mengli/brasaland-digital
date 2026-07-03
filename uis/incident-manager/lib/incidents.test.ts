import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const INCIDENTS_BASE = 'http://localhost:3004/api/incidents';

describe('incidents client', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_INCIDENTS_API_URL', INCIDENTS_BASE);
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('getIncidents calls the list URL without auth', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    const { getIncidents } = await import('./incidents');
    await getIncidents();

    expect(fetchMock).toHaveBeenCalledWith(`${INCIDENTS_BASE}`, undefined);
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.headers).toBeUndefined();
  });

  it('getIncidents appends filter query params', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    const { getIncidents } = await import('./incidents');
    await getIncidents({ status: 'open', branch: 'COL-01' });

    expect(fetchMock).toHaveBeenCalledWith(
      `${INCIDENTS_BASE}?status=open&branch=COL-01`,
      undefined,
    );
  });

  it('createIncident POSTs JSON without Authorization header', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1, status: 'open' }), { status: 201 }),
    );

    const { createIncident } = await import('./incidents');
    await createIncident({
      title: 'Grill issue',
      description: 'Undercooked steak',
      category: 'QUEJA_CLIENTE',
      origin: 'customer',
      branch: 'COL-01',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${INCIDENTS_BASE}`,
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it('updateStatus PATCHes the status endpoint', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1, status: 'in_progress' }), { status: 200 }),
    );

    const { updateStatus } = await import('./incidents');
    await updateStatus(1, 'in_progress');

    expect(fetchMock).toHaveBeenCalledWith(
      `${INCIDENTS_BASE}/1/status`,
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ status: 'in_progress' }),
      }),
    );
  });

  it('propagates API error messages from parseApiError', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Incident not found' }), {
        status: 404,
        statusText: 'Not Found',
      }),
    );

    const { getIncident } = await import('./incidents');
    await expect(getIncident(999)).rejects.toThrow('Incident not found');
  });

  it('throws CreateIncidentError with field errors on validation failure', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail: {
            errors: [{ field: 'title', message: 'title is required' }],
          },
        }),
        { status: 400, statusText: 'Bad Request' },
      ),
    );

    const { createIncident, CreateIncidentError } = await import('./incidents');

    await expect(
      createIncident({
        title: '',
        description: 'Test',
        category: 'QUEJA_CLIENTE',
        origin: 'customer',
        branch: 'COL-01',
      }),
    ).rejects.toSatisfy((error: unknown) => {
      return (
        error instanceof CreateIncidentError &&
        error.fieldErrors.length === 1 &&
        error.fieldErrors[0]?.field === 'title'
      );
    });
  });
});
