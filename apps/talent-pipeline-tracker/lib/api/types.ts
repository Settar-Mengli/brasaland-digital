/**
 * Domain types for the talent pipeline tracker API.
 * Field names mirror the backend's snake_case wire format intentionally —
 * no camelCase transformation so there is a single source of truth.
 */

/** Lifecycle status of a candidate application. */
export type CandidateStatus = 'received' | 'in_progress' | 'selected' | 'discarded';

/** Current stage in the hiring pipeline. */
export type CandidateStage =
  | 'pending'
  | 'review'
  | 'personal_interview'
  | 'technical_interview'
  | 'offer_presented';

/**
 * A single candidate record as returned by the API.
 * All field names are snake_case to match the wire format.
 */
export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  /** URL to the candidate's LinkedIn profile, or null if not provided. */
  linkedin_url: string | null;
  /** URL to the candidate's uploaded CV, or null if not provided. */
  cv_url: string | null;
  experience_years: number;
  status: CandidateStatus;
  stage: CandidateStage;
  /** ISO 8601 timestamp — when the candidate applied. */
  applied_at: string;
  /** ISO 8601 timestamp. */
  updated_at: string;
  /** Notes attached to this candidate (returned inline by GET /records). */
  notes?: Note[];
  /** Count of notes attached to this candidate (returned inline by GET /records). */
  notes_count?: number;
}

/**
 * An interviewer note attached to a candidate record.
 * All field names are snake_case to match the wire format.
 */
export interface Note {
  id: string;
  /** ID of the candidate (called a "record" in the API's domain language). */
  record_id: string;
  content: string;
  /** ISO 8601 timestamp. */
  created_at: string;
}

/**
 * Body of the business-rule 422 error shape returned by the backend.
 * Shape: `{ "error": "Invalid value", "details": { "status": "...", "stage": "..." } }`.
 */
export interface BusinessRuleErrorBody {
  error: string;
  details: {
    status?: string;
    stage?: string;
  };
}

/** A single validation error entry from FastAPI's schema 422 response. */
export interface SchemaErrorEntry {
  /** JSON path identifying the invalid field, e.g. `["body", "status"]`. */
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * Body of the FastAPI schema 422 error shape.
 * Shape: `{ "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }`.
 */
export interface SchemaErrorBody {
  detail: SchemaErrorEntry[];
}

/**
 * Paginated response envelope returned by list endpoints.
 * Verified shape from `GET /records?limit=2`.
 */
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  limit: number;
  data: T[];
}

/**
 * Collection response envelope for endpoints that return a full list
 * with a count summary but no pagination metadata.
 * Verified shape from `GET /records/{id}/notes`.
 *
 * Distinct from `PaginatedResponse<T>`, which carries `total`, `page`,
 * and `limit` at the top level for paginated endpoints like `/records`.
 */
export interface CollectionResponse<T> {
  data: T[];
  meta: {
    total: number;
  };
}
