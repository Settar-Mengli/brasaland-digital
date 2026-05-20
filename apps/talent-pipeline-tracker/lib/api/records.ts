/**
 * Endpoint wrappers for the `/records` resource.
 * All return parsed JSON or throw ApiError via apiFetch.
 */

import type { Candidate, CandidateStatus, CandidateStage } from './types';
import { apiFetch } from './client';

/** Filter parameters accepted by `GET /records`. */
export interface ListCandidatesFilters {
  status?: CandidateStatus;
  stage?: CandidateStage;
  /** Free-text search across candidate fields. */
  search?: string;
  page?: number;
  limit?: number;
}

/**
 * Body shape for creating a candidate.
 * Server generates id, status, stage, created_at, and updated_at.
 */
export interface CreateCandidateInput {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url?: string | null;
  cv_url?: string | null;
  experience_years: number;
}

/**
 * Partial body shape for PATCH /records/{id}. At least one of status or stage
 * must be provided to produce a meaningful update.
 */
export interface UpdateCandidateStatusStageInput {
  status?: CandidateStatus;
  stage?: CandidateStage;
}

/** List candidates, optionally filtered. */
export async function listCandidates(filters: ListCandidatesFilters = {}): Promise<Candidate[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.stage) params.set('stage', filters.stage);
  if (filters.search) params.set('search', filters.search);
  if (filters.page !== undefined) params.set('page', String(filters.page));
  if (filters.limit !== undefined) params.set('limit', String(filters.limit));
  const query = params.toString();
  const path = query ? `/records?${query}` : '/records';
  return apiFetch<Candidate[]>(path);
}

/** Fetch a single candidate by id. */
export async function getCandidate(id: string): Promise<Candidate> {
  return apiFetch<Candidate>(`/records/${encodeURIComponent(id)}`);
}

/** Create a new candidate. */
export async function createCandidate(input: CreateCandidateInput): Promise<Candidate> {
  return apiFetch<Candidate>('/records', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/** Update a candidate's status and/or stage. */
export async function updateCandidateStatusStage(
  id: string,
  patch: UpdateCandidateStatusStageInput,
): Promise<Candidate> {
  return apiFetch<Candidate>(`/records/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}
