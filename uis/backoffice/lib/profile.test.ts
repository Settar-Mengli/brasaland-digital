import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const AUTH_BASE = 'http://localhost/staff/api/auth';

describe('profile client', () => {
  const assignMock = vi.fn();

  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_AUTH_API_URL', AUTH_BASE);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'test-access-token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    });
    vi.stubGlobal('window', {
      ...globalThis,
      localStorage,
      location: { assign: assignMock },
    });
    vi.stubGlobal('fetch', vi.fn());
    assignMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('getProfile GETs /profiles/me with Bearer token', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          email: 'ops@brasaland.com',
          name: 'Settar',
          phone: '',
          address: '',
        }),
        { status: 200 },
      ),
    );

    const { getProfile } = await import('./profile');
    const profile = await getProfile();

    expect(profile.email).toBe('ops@brasaland.com');
    expect(fetchMock).toHaveBeenCalledWith(
      `${AUTH_BASE}/profiles/me`,
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );
    const [, init] = fetchMock.mock.calls[0]!;
    const headers = new Headers(init?.headers);
    expect(headers.get('Authorization')).toBe('Bearer test-access-token');
  });

  it('updateProfile PUTs /profiles/me with Bearer and JSON body', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          email: 'ops@brasaland.com',
          name: 'Updated',
          phone: '123',
          address: 'Calle 1',
        }),
        { status: 200 },
      ),
    );

    const { updateProfile } = await import('./profile');
    await updateProfile({ name: 'Updated', phone: '123', address: 'Calle 1' });

    expect(fetchMock).toHaveBeenCalledWith(
      `${AUTH_BASE}/profiles/me`,
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ name: 'Updated', phone: '123', address: 'Calle 1' }),
      }),
    );
    const [, init] = fetchMock.mock.calls[0]!;
    const headers = new Headers(init?.headers);
    expect(headers.get('Authorization')).toBe('Bearer test-access-token');
    expect(headers.get('Content-Type')).toBe('application/json');
  });
});
