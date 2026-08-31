import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('handleUnauthorized', () => {
  const assignMock = vi.fn();

  beforeEach(() => {
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
    assignMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it('clears the token and redirects to /login on 401', async () => {
    const { handleUnauthorized } = await import('./session');

    expect(() => handleUnauthorized(new Response(null, { status: 401 }))).toThrow('Unauthorized');
    expect(localStorage.removeItem).toHaveBeenCalledWith('brasaland_access_token');
    expect(assignMock).toHaveBeenCalledWith('/staff/login');
  });

  it('does nothing for non-401 responses', async () => {
    const { handleUnauthorized } = await import('./session');

    expect(() => handleUnauthorized(new Response(null, { status: 403 }))).not.toThrow();
    expect(localStorage.removeItem).not.toHaveBeenCalled();
    expect(assignMock).not.toHaveBeenCalled();
  });
});
