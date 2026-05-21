/** Public surface of the talent pipeline API client. */

export type {
  Candidate,
  CandidateStatus,
  CandidateStage,
  Note,
  BusinessRuleErrorBody,
  SchemaErrorBody,
  SchemaErrorEntry,
  PaginatedResponse,
  CollectionResponse,
} from './types';
export { STATUS_LABELS, STAGE_LABELS } from './labels';
export { ApiError, apiFetch } from './client';
export type { ApiErrorKind } from './client';
export {
  listCandidates,
  getCandidate,
  createCandidate,
  updateCandidateStatusStage,
} from './records';
export type {
  ListCandidatesFilters,
  CreateCandidateInput,
  UpdateCandidateStatusStageInput,
} from './records';
export { listNotes, createNote, deleteNote } from './notes';
