import { parseApiError } from './api-error';
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
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
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

export function createIncident(body: IncidentCreateInput): Promise<Incident> {
  return incidentsFetch<Incident>('', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
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
