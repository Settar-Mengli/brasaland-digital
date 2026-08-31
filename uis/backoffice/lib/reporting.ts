import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import { resolveStaffApiBase } from './staff-paths';
import type { PipelineRunResponse, WeeklyLocationPerformanceResponse } from './reporting-types';

function getReportingBaseUrl(): string {
  return resolveStaffApiBase('reporting', 'NEXT_PUBLIC_REPORTING_API_URL');
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
