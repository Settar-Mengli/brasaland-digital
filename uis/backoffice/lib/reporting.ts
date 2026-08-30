import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import type { PipelineRunResponse, WeeklyLocationPerformanceResponse } from './reporting-types';

/**
 * Same-origin reporting API base (rewritten to REPORTING_API_ORIGIN).
 */
function getReportingBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_REPORTING_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_REPORTING_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

async function reportingFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${getReportingBaseUrl()}${path}`, {
    ...init,
    headers,
  });
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
}

/**
 * Fetch weekly location KPI rows. Omitting weekStart uses the latest computed week.
 */
export function getWeeklyLocationPerformance(
  weekStart?: string,
): Promise<WeeklyLocationPerformanceResponse> {
  const params = weekStart ? `?week_start=${encodeURIComponent(weekStart)}` : '';
  return reportingFetch<WeeklyLocationPerformanceResponse>(`/weekly-location-performance${params}`);
}

/**
 * Fetch metadata for the most recent pipeline run (structured nulls when none).
 */
export function getLatestPipelineRun(): Promise<PipelineRunResponse> {
  return reportingFetch<PipelineRunResponse>('/pipeline-runs/latest');
}
