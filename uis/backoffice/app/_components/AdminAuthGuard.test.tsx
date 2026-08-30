/** @vitest-environment jsdom */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const replaceMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

vi.mock('@/lib/auth', () => ({
  clearAccessToken: vi.fn(),
  getAccessToken: vi.fn(),
  isAdminAccessToken: vi.fn(),
}));

vi.mock('@/lib/telemetry', () => ({
  isAccessTokenExpired: vi.fn(),
}));

import AdminAuthGuard from '@/app/_components/AdminAuthGuard';
import { clearAccessToken, getAccessToken, isAdminAccessToken } from '@/lib/auth';
import { isAccessTokenExpired } from '@/lib/telemetry';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  replaceMock.mockReset();
  vi.mocked(isAccessTokenExpired).mockReturnValue(false);
});

describe('AdminAuthGuard', () => {
  it('redirects an unauthenticated visitor to login', async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);

    render(
      <AdminAuthGuard>
        <p>Admin content</p>
      </AdminAuthGuard>,
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/login');
    });
    expect(screen.queryByText('Admin content')).toBeNull();
  });

  it('clears an expired token and redirects to login', async () => {
    vi.mocked(getAccessToken).mockReturnValue('expired-token');
    vi.mocked(isAccessTokenExpired).mockReturnValue(true);

    render(
      <AdminAuthGuard>
        <p>Admin content</p>
      </AdminAuthGuard>,
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/login');
    });
    expect(clearAccessToken).toHaveBeenCalled();
  });

  it('redirects an authenticated non-admin to the dashboard', async () => {
    vi.mocked(getAccessToken).mockReturnValue('non-admin-token');
    vi.mocked(isAdminAccessToken).mockReturnValue(false);

    render(
      <AdminAuthGuard>
        <p>Admin content</p>
      </AdminAuthGuard>,
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/');
    });
    expect(screen.queryByText('Admin content')).toBeNull();
  });

  it('renders the reporting surface for an admin token', async () => {
    vi.mocked(getAccessToken).mockReturnValue('admin-token');
    vi.mocked(isAdminAccessToken).mockReturnValue(true);

    render(
      <AdminAuthGuard>
        <p>Admin content</p>
      </AdminAuthGuard>,
    );

    expect(await screen.findByText('Admin content')).not.toBeNull();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
