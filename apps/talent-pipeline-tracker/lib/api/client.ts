/**
 * Base HTTP client for the talent pipeline tracker API.
 * Discriminates between the two 422 error shapes the backend returns and
 * throws a typed ApiError on any non-2xx response or network failure.
 */

import type { BusinessRuleErrorBody, SchemaErrorBody, SchemaErrorEntry } from './types';

export type ApiErrorKind = 'business' | 'schema' | 'network';

/**
 * Typed error thrown by apiFetch on any non-2xx response or network failure.
 * Discriminate by `kind`:
 *   - 'business': backend returned a custom 422 with details.status / details.stage
 *   - 'schema': backend returned a FastAPI 422 with detail[] entries
 *   - 'network': non-422 HTTP error, network failure, or missing env config
 */
export class ApiError extends Error {
  readonly status: number;
  readonly kind: ApiErrorKind;
  readonly details?: BusinessRuleErrorBody['details'] | SchemaErrorEntry[];

  constructor(
    message: string,
    status: number,
    kind: ApiErrorKind,
    details?: BusinessRuleErrorBody['details'] | SchemaErrorEntry[],
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.kind = kind;
    this.details = details;
  }
}

/** Type guard: is this body the business-rule 422 shape? */
function isBusinessRuleError(body: unknown): body is BusinessRuleErrorBody {
  if (typeof body !== 'object' || body === null) return false;
  const b = body as Record<string, unknown>;
  return typeof b.error === 'string' && typeof b.details === 'object' && b.details !== null;
}

/** Type guard: is this body the FastAPI schema 422 shape? */
function isSchemaError(body: unknown): body is SchemaErrorBody {
  if (typeof body !== 'object' || body === null) return false;
  const b = body as Record<string, unknown>;
  return Array.isArray(b.detail);
}

/**
 * Fetch a JSON resource from the talent pipeline backend.
 * Throws ApiError on any non-2xx response or network failure.
 * Returns the parsed JSON body, or undefined for 204 No Content.
 *
 * @param path - path beginning with '/' (e.g. '/records' or '/records/abc/notes')
 * @param init - standard fetch init; Content-Type defaults to application/json
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new ApiError(
      'NEXT_PUBLIC_API_URL is not configured. Copy .env.example to .env.local.',
      0,
      'network',
    );
  }

  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError('Network request failed', 0, 'network');
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // response not JSON; leave body null
    }

    if (response.status === 422 && isBusinessRuleError(body)) {
      throw new ApiError(body.error, 422, 'business', body.details);
    }
    if (response.status === 422 && isSchemaError(body)) {
      throw new ApiError('Validation failed', 422, 'schema', body.detail);
    }
    throw new ApiError(
      `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      'network',
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError('Invalid response from server', response.status, 'schema');
  }
}
