import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearSessionLocationSlug,
  getSessionLocationId,
  LOCATION_MAP,
  LOCATION_SLUG_KEY,
  locationSlug,
  readLocationSlugFromAccessToken,
  setSessionLocationSlug,
} from './locations';

function makeJwt(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.signature`;
}

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

describe('locations', () => {
  it('maps all 14 form values to slugs', () => {
    expect(Object.keys(LOCATION_MAP)).toHaveLength(14);
    expect(locationSlug(1)).toBe('medellin_centro');
    expect(locationSlug('14')).toBe('miami_kendall');
  });

  it('throws for unknown form values', () => {
    expect(() => locationSlug(0)).toThrow();
    expect(() => locationSlug(99)).toThrow();
  });

  describe('session location', () => {
    beforeEach(() => {
      const storage = createStorage();
      const sessionStore = createStorage();
      vi.stubGlobal('localStorage', storage);
      vi.stubGlobal('sessionStorage', sessionStore);
      vi.stubGlobal('window', {
        ...globalThis,
        localStorage: storage,
        sessionStorage: sessionStore,
      });
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it('returns id from session slug', () => {
      setSessionLocationSlug('miami_brickell');
      expect(getSessionLocationId()).toBe(11);
    });

    it('hydrates session slug from JWT when session is empty', () => {
      localStorage.setItem('brasaland_access_token', makeJwt({ location_slug: 'medellin_centro' }));
      expect(getSessionLocationId()).toBe(1);
      expect(sessionStorage.getItem(LOCATION_SLUG_KEY)).toBe('medellin_centro');
    });

    it('throws when session and JWT lack location', () => {
      expect(() => getSessionLocationId()).toThrow(
        'Session location is not set. Sign in again and choose a location.',
      );
    });

    it('clears session slug', () => {
      setSessionLocationSlug('miami_brickell');
      clearSessionLocationSlug();
      expect(sessionStorage.getItem(LOCATION_SLUG_KEY)).toBeNull();
    });

    it('readLocationSlugFromAccessToken returns slug from token', () => {
      localStorage.setItem(
        'brasaland_access_token',
        makeJwt({ location_slug: 'bogota_chapinero' }),
      );
      expect(readLocationSlugFromAccessToken()).toBe('bogota_chapinero');
    });
  });
});
