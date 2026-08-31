import { clearAccessToken } from './auth';
import { staffLoginPath } from './staff-paths';

/**
 * Shared 401 handler for authenticated API clients.
 * Clears the access token and hard-navigates to /login.
 * Do not call from login() or register().
 */
export function handleUnauthorized(response: Response): void {
  if (response.status !== 401) {
    return;
  }
  clearAccessToken();
  window.location.assign(staffLoginPath());
  throw new Error('Unauthorized');
}
