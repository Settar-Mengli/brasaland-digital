import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const AUTH_BASE = 'http://localhost:3003/api/auth';

function createStorage() {
  const store = new Map<string, string>();
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value);
    }),
    removeItem: vi.fn((key: string) => {
      store.delete(key);
    }),
    clear: vi.fn(() => {
      store.clear();
    }),
    key: vi.fn(),
    length: 0,
  };
}

describe('auth client', () => {
  const assignMock = vi.fn();

  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_AUTH_API_URL', AUTH_BASE);
    const storage = createStorage();
    vi.stubGlobal('localStorage', storage);
    vi.stubGlobal('window', {
      ...globalThis,
      localStorage: storage,
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

  it('register POSTs JSON to /register and stores access_token', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          token_type: 'bearer',
        }),
        { status: 201 },
      ),
    );

    const { register } = await import('./auth');
    await register('ops@brasaland.com', 'password123', {
      name: 'Settar',
      phone: '555',
      address: 'Medellín',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${AUTH_BASE}/register`,
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'ops@brasaland.com',
          password: 'password123',
          name: 'Settar',
          phone: '555',
          address: 'Medellín',
        }),
      }),
    );
    expect(localStorage.setItem).toHaveBeenCalledWith('brasaland_access_token', 'new-access-token');
  });

  it('logout clears the token and assigns /login', async () => {
    localStorage.setItem('brasaland_access_token', 'to-clear');

    const { logout } = await import('./auth');
    logout();

    expect(localStorage.removeItem).toHaveBeenCalledWith('brasaland_access_token');
    expect(assignMock).toHaveBeenCalledWith('/login');
  });

  it('defaults auth base to /api/auth when NEXT_PUBLIC_AUTH_API_URL is unset', async () => {
    vi.unstubAllEnvs();
    vi.resetModules();
    const fetchMock = vi.fn().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          access_token: 'rel-token',
          refresh_token: 'rel-refresh',
          token_type: 'bearer',
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    const { login } = await import('./auth');
    await login('ops@brasaland.com', 'password123');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({ method: 'POST' }),
    );
  });
});
