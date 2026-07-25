import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';

export type Profile = {
  email: string;
  name: string;
  phone: string;
  address: string;
};

export type ProfileUpdate = {
  name?: string;
  phone?: string;
  address?: string;
};

function getAuthBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_AUTH_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_AUTH_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

async function profileFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${getAuthBaseUrl()}${path}`, {
    ...init,
    headers,
  });

  handleUnauthorized(response);

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  return response.json() as Promise<T>;
}

export function getProfile(): Promise<Profile> {
  return profileFetch<Profile>('/profiles/me');
}

export function updateProfile(fields: ProfileUpdate): Promise<Profile> {
  return profileFetch<Profile>('/profiles/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
}
