import { parseApiError } from './api-error';
import type { AuthorizedLocationsResponse, TokenResponse } from './inventory-types';
import { setSessionLocationSlug } from './locations';

const TOKEN_KEY = 'brasaland_access_token';

export type RegisterProfile = {
  name?: string;
  phone?: string;
  address?: string;
};

/**
 * Same-origin auth API base (rewritten to AUTH_API_ORIGIN).
 * Defaults to `/api/auth` so production images need no baked hostname.
 */
export function getAuthBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_AUTH_API_URL;
  if (url === undefined || url === '') {
    return '/api/auth';
  }
  return url.replace(/\/$/, '');
}

export async function fetchAuthorizedLocations(
  email: string,
  password: string,
): Promise<AuthorizedLocationsResponse> {
  const response = await fetch(`${getAuthBaseUrl()}/login/authorized-locations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  return (await response.json()) as AuthorizedLocationsResponse;
}

export async function login(email: string, password: string, locationSlug: string): Promise<void> {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);
  body.set('location_slug', locationSlug);

  const response = await fetch(`${getAuthBaseUrl()}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  const data = (await response.json()) as TokenResponse;
  setAccessToken(data.access_token);
  setSessionLocationSlug(data.location_slug ?? locationSlug);
}

export async function register(
  email: string,
  password: string,
  profile?: RegisterProfile,
): Promise<void> {
  const body: Record<string, string> = { email, password };
  if (profile?.name) {
    body.name = profile.name;
  }
  if (profile?.phone) {
    body.phone = profile.phone;
  }
  if (profile?.address) {
    body.address = profile.address;
  }

  const response = await fetch(`${getAuthBaseUrl()}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  const data = (await response.json()) as TokenResponse;
  setAccessToken(data.access_token);
}

export function logout(): void {
  clearAccessToken();
  window.location.assign('/login');
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}
