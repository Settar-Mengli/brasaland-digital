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
}));

vi.mock('@/lib/telemetry', () => ({
  clearTelemetrySessionKeys: vi.fn(),
  computeIdleDurationMs: vi.fn(() => 0),
  hasTelemetrySessionEvidence: vi.fn(() => false),
  isAccessTokenExpired: vi.fn(() => false),
  shouldEmitSessionExpired: vi.fn(() => false),
  track: vi.fn(),
}));

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { clearAccessToken, getAccessToken } from '@/lib/auth';
import { isAccessTokenExpired } from '@/lib/telemetry';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  replaceMock.mockReset();
});

describe('InventoryAuthGuard', () => {
  it('redirects to /login when access token missing', async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);

    render(
      <InventoryAuthGuard>
        <p>Protected content</p>
      </InventoryAuthGuard>,
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/login');
    });
    expect(screen.queryByText('Protected content')).toBeNull();
  });

  it('redirects to /login when token expired', async () => {
    vi.mocked(getAccessToken).mockReturnValue('expired-token');
    vi.mocked(isAccessTokenExpired).mockReturnValue(true);

    render(
      <InventoryAuthGuard>
        <p>Protected content</p>
      </InventoryAuthGuard>,
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith('/login');
    });
    expect(clearAccessToken).toHaveBeenCalled();
  });

  it('renders children when token valid', async () => {
    vi.mocked(getAccessToken).mockReturnValue('valid-token');
    vi.mocked(isAccessTokenExpired).mockReturnValue(false);

    render(
      <InventoryAuthGuard>
        <p>Protected content</p>
      </InventoryAuthGuard>,
    );

    expect(await screen.findByText('Protected content')).not.toBeNull();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
