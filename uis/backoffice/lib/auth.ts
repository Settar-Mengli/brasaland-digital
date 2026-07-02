import { parseApiError } from './api-error';
import type { TokenResponse } from './inventory-types';

const TOKEN_KEY = 'brasaland_access_token';

function getAuthBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_AUTH_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_AUTH_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);

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
