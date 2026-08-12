import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import type { RfpTicket, RfpUploadResponse } from './rfp-types';

/**
 * Same-origin RFP API base (rewritten to RFP_API_ORIGIN).
 */
function getRfpBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_RFP_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_RFP_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

function requireAccessToken(): string {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  return token;
}

/**
 * Upload an RFP PDF. Requires a Bearer JWT. Do not set Content-Type (multipart boundary).
 */
export async function uploadRfp(file: File): Promise<RfpUploadResponse> {
  const token = requireAccessToken();
  const body = new FormData();
  body.append('file', file);
  const response = await fetch(`${getRfpBaseUrl()}/tickets`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body,
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpUploadResponse;
}

/**
 * Poll ticket row status. Requires a Bearer JWT.
 */
export async function getRfpTicket(ticketId: string): Promise<RfpTicket> {
  const token = requireAccessToken();
  const response = await fetch(`${getRfpBaseUrl()}/tickets/${ticketId}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpTicket;
}
