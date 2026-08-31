/** @vitest-environment jsdom */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const pathnameMock = vi.fn(() => '/inventory/products');

vi.mock('next/navigation', () => ({
  usePathname: () => pathnameMock(),
}));

vi.mock('@/lib/auth', () => ({
  getAccessToken: vi.fn(),
  logout: vi.fn(),
}));

vi.mock('@/lib/telemetry', () => ({
  isAccessTokenExpired: vi.fn(() => false),
}));

import NavLinks from '@/app/_components/NavLinks';
import { getAccessToken } from '@/lib/auth';
import { isAccessTokenExpired } from '@/lib/telemetry';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  pathnameMock.mockReturnValue('/inventory/products');
});

describe('NavLinks', () => {
  it('renders nothing on /login when logged out', async () => {
    pathnameMock.mockReturnValue('/login');
    vi.mocked(getAccessToken).mockReturnValue(null);

    render(<NavLinks />);

    await waitFor(() => {
      expect(screen.queryByRole('navigation', { name: 'Backoffice navigation' })).toBeNull();
    });
    expect(screen.queryByRole('button', { name: 'Logout' })).toBeNull();
  });

  it('renders nothing on /register when logged out', async () => {
    pathnameMock.mockReturnValue('/register');
    vi.mocked(getAccessToken).mockReturnValue(null);

    render(<NavLinks />);

    await waitFor(() => {
      expect(screen.queryByRole('navigation', { name: 'Backoffice navigation' })).toBeNull();
    });
  });

  it('renders app nav when session is valid', async () => {
    vi.mocked(getAccessToken).mockReturnValue('valid-token');
    vi.mocked(isAccessTokenExpired).mockReturnValue(false);

    render(<NavLinks />);

    expect(await screen.findByRole('navigation', { name: 'Backoffice navigation' })).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Logout' })).not.toBeNull();
    expect(screen.getByRole('link', { name: 'Inventory' })).not.toBeNull();
  });
});
