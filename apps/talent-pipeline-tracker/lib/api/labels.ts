/**
 * Display labels for status and stage enums.
 * Raw API values (e.g. `in_progress`, `personal_interview`) must never appear
 * in the UI — always go through these maps.
 *
 * Typed as `Record<Union, string>` so TypeScript errors at compile time if a
 * union member is missing or an unrecognised key is added.
 */

import type { CandidateStatus, CandidateStage } from './types';

export const STATUS_LABELS: Record<CandidateStatus, string> = {
  received: 'Received',
  in_progress: 'In progress',
  selected: 'Selected',
  discarded: 'Discarded',
};

export const STAGE_LABELS: Record<CandidateStage, string> = {
  pending: 'Pending review',
  review: 'Under review',
  personal_interview: 'Personal interview',
  technical_interview: 'Technical interview',
  offer_presented: 'Offer presented',
};
