import { parseApiErrorResponse, type FieldError } from './api-error';
import type {
  Incident,
  IncidentCreateInput,
  IncidentListFilters,
  IncidentStatus,
  IncidentSummary,
} from './incident-types';

function getIncidentsBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_INCIDENTS_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_INCIDENTS_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

async function incidentsFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getIncidentsBaseUrl()}${path}`, init);
  if (!response.ok) {
    const parsed = await parseApiErrorResponse(response);
    throw new Error(parsed.message);
  }
  return response.json() as Promise<T>;
}

export class CreateIncidentError extends Error {
  readonly fieldErrors: FieldError[];

  constructor(message: string, fieldErrors: FieldError[]) {
    super(message);
    this.name = 'CreateIncidentError';
    this.fieldErrors = fieldErrors;
  }
}

export async function createIncident(body: IncidentCreateInput): Promise<Incident> {
  const response = await fetch(`${getIncidentsBaseUrl()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const parsed = await parseApiErrorResponse(response);
    if (parsed.fieldErrors.length > 0) {
      throw new CreateIncidentError(parsed.message, parsed.fieldErrors);
    }
    throw new Error(parsed.message);
  }

  return response.json() as Promise<Incident>;
}

function buildQueryString(filters: IncidentListFilters): string {
  const params = new URLSearchParams();
  if (filters.status !== undefined) {
    params.set('status', filters.status);
  }
  if (filters.origin !== undefined) {
    params.set('origin', filters.origin);
  }
  if (filters.branch !== undefined) {
    params.set('branch', filters.branch);
  }
  if (filters.category !== undefined) {
    params.set('category', filters.category);
  }
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function getIncidents(filters: IncidentListFilters = {}): Promise<Incident[]> {
  return incidentsFetch<Incident[]>(buildQueryString(filters));
}

export function getIncident(id: number): Promise<Incident> {
  return incidentsFetch<Incident>(`/${id}`);
}

export function updateStatus(id: number, status: IncidentStatus): Promise<Incident> {
  return incidentsFetch<Incident>(`/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
}

export function getSummary(): Promise<IncidentSummary> {
  return incidentsFetch<IncidentSummary>('/summary');
}
