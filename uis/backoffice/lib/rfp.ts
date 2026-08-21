import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import type {
  RfpCeoDecisionResponse,
  RfpSectionDecisionResponse,
  RfpTicket,
  RfpUploadResponse,
} from './rfp-types';

/**
 * Same-origin RFP API base (rewritten to RFP_API_ORIGIN).
 * Defaults to `/api/rfp` so production images need no baked hostname.
 */
function getRfpBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_RFP_API_URL;
  if (url === undefined || url === '') {
    return '/api/rfp';
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

/**
 * Trigger response generation for an intake_complete ticket. Requires a Bearer JWT.
 */
export async function triggerRfpResponse(ticketId: string): Promise<RfpUploadResponse> {
  const token = requireAccessToken();
  const response = await fetch(`${getRfpBaseUrl()}/tickets/${ticketId}/response`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpUploadResponse;
}

/**
 * Start approval for an under_evaluation ticket. Requires a Bearer JWT.
 */
export async function startRfpApproval(ticketId: string): Promise<RfpUploadResponse> {
  const token = requireAccessToken();
  const response = await fetch(`${getRfpBaseUrl()}/tickets/${ticketId}/approval`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpUploadResponse;
}

/**
 * Approve or reject one department section. Requires a Bearer JWT.
 * Omits `feedback` when absent or blank (exactOptionalPropertyTypes).
 */
export async function decideRfpSection(
  ticketId: string,
  departmentId: string,
  action: 'approve' | 'reject' | 'request_changes',
  feedback?: string,
): Promise<RfpSectionDecisionResponse> {
  const token = requireAccessToken();
  const trimmed = feedback?.trim() ?? '';
  const body: { action: string; feedback?: string } = { action };
  if (trimmed.length > 0) {
    body.feedback = trimmed;
  }
  const response = await fetch(
    `${getRfpBaseUrl()}/tickets/${ticketId}/sections/${departmentId}/decision`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    },
  );
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpSectionDecisionResponse;
}

/**
 * CEO approve or reject. Requires a Bearer JWT.
 */
export async function decideRfpCeo(
  ticketId: string,
  action: 'approve' | 'reject',
): Promise<RfpCeoDecisionResponse> {
  const token = requireAccessToken();
  const response = await fetch(`${getRfpBaseUrl()}/tickets/${ticketId}/ceo/decision`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ action }),
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return (await response.json()) as RfpCeoDecisionResponse;
}
