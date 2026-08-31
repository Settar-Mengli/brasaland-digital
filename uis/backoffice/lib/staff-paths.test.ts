import { afterEach, describe, expect, it, vi } from 'vitest';

import { resolveStaffApiBase, staffLoginPath, staffPath } from './staff-paths';

describe('staff-paths', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('staffPath prefixes routes with the staff mount', () => {
    expect(staffPath('/login')).toBe('/staff/login');
    expect(staffPath('inventory/products')).toBe('/staff/inventory/products');
  });

  it('staffLoginPath returns the login route under staff', () => {
    expect(staffLoginPath()).toBe('/staff/login');
  });

  it('resolveStaffApiBase uses explicit env when set', () => {
    vi.stubEnv('NEXT_PUBLIC_AUTH_API_URL', 'http://localhost/staff/api/auth');
    expect(resolveStaffApiBase('auth', 'NEXT_PUBLIC_AUTH_API_URL')).toBe(
      'http://localhost/staff/api/auth',
    );
  });

  it('resolveStaffApiBase defaults under staff when env unset', () => {
    vi.stubEnv('NEXT_PUBLIC_AUTH_API_URL', '');
    expect(resolveStaffApiBase('inventory', 'NEXT_PUBLIC_INVENTORY_API_URL')).toBe(
      '/staff/api/inventory',
    );
  });

  it('resolveStaffApiBase normalizes legacy /api paths without staff mount', () => {
    vi.stubEnv('NEXT_PUBLIC_INVENTORY_API_URL', 'http://localhost:3003/api/inventory');
    expect(resolveStaffApiBase('inventory', 'NEXT_PUBLIC_INVENTORY_API_URL')).toBe(
      'http://localhost:3003/staff/api/inventory',
    );
  });

  it('resolveStaffApiBase normalizes path-only legacy /api paths', () => {
    vi.stubEnv('NEXT_PUBLIC_AUTH_API_URL', '/api/auth');
    expect(resolveStaffApiBase('auth', 'NEXT_PUBLIC_AUTH_API_URL')).toBe('/staff/api/auth');
  });
});
