import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('./auth', () => ({
  getAccessToken: vi.fn(),
}));

vi.mock('./session', () => ({
  handleUnauthorized: vi.fn(),
}));

vi.mock('./api-error', () => ({
  parseApiError: vi.fn(async () => 'api error'),
}));

import { parseApiError } from './api-error';
import { getAccessToken } from './auth';
import { getRfpTicket, triggerRfpResponse, uploadRfp } from './rfp';
import { handleUnauthorized } from './session';

describe('uploadRfp', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('posts FormData to /tickets with Bearer and no Content-Type', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({
        ticket_id: 't1',
        rfp_id: 'r1',
        status: 'analyzing',
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const file = new File(['%PDF-1.4'], 'seed.pdf', { type: 'application/pdf' });
    const result = await uploadRfp(file);

    expect(result).toEqual({
      ticket_id: 't1',
      rfp_id: 'r1',
      status: 'analyzing',
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:3003/api/rfp/tickets',
      expect.objectContaining({
        method: 'POST',
        headers: { Authorization: 'Bearer tok' },
        body: expect.any(FormData),
      }),
    );
    const call = fetchMock.mock.calls[0]![1] as RequestInit;
    expect(call.headers).not.toHaveProperty('Content-Type');
    expect(handleUnauthorized).toHaveBeenCalled();
  });

  it('throws when not authenticated', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue(null);
    const file = new File(['%PDF-1.4'], 'seed.pdf', { type: 'application/pdf' });
    await expect(uploadRfp(file)).rejects.toThrow('Not authenticated');
  });

  it('calls handleUnauthorized and throws parseApiError on !ok', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 413,
      json: async () => ({ detail: 'too large' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const file = new File(['%PDF-1.4'], 'seed.pdf', { type: 'application/pdf' });
    await expect(uploadRfp(file)).rejects.toThrow('api error');
    expect(handleUnauthorized).toHaveBeenCalled();
    expect(parseApiError).toHaveBeenCalled();
  });
});

describe('getRfpTicket', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('GETs /tickets/{id} with Bearer and returns the ticket', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const ticket = {
      ticket_id: 't1',
      rfp_id: 'r1',
      status: 'intake_complete',
      created_at: '2026-01-01T00:00:00+00:00',
      updated_at: '2026-01-01T00:01:00+00:00',
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ticket,
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await getRfpTicket('t1');

    expect(result).toEqual(ticket);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:3003/api/rfp/tickets/t1',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer tok',
        }),
      }),
    );
    expect(handleUnauthorized).toHaveBeenCalled();
  });

  it('calls handleUnauthorized and throws parseApiError on !ok', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'not found' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getRfpTicket('missing')).rejects.toThrow('api error');
    expect(handleUnauthorized).toHaveBeenCalled();
    expect(parseApiError).toHaveBeenCalled();
  });
});

describe('triggerRfpResponse', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('POSTs /tickets/{id}/response with Bearer and no body Content-Type', async () => {
    vi.stubEnv('NEXT_PUBLIC_RFP_API_URL', 'http://localhost:3003/api/rfp');
    vi.mocked(getAccessToken).mockReturnValue('tok');
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({
        ticket_id: 't1',
        rfp_id: 'r1',
        status: 'intake_complete',
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await triggerRfpResponse('t1');

    expect(result).toEqual({
      ticket_id: 't1',
      rfp_id: 'r1',
      status: 'intake_complete',
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:3003/api/rfp/tickets/t1/response',
      expect.objectContaining({
        method: 'POST',
        headers: { Authorization: 'Bearer tok' },
      }),
    );
    const call = fetchMock.mock.calls[0]![1] as RequestInit;
    expect(call.headers).not.toHaveProperty('Content-Type');
    expect(call).not.toHaveProperty('body');
    expect(handleUnauthorized).toHaveBeenCalled();
  });
});
