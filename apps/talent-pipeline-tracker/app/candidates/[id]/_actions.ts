'use server';

import { revalidatePath } from 'next/cache';
import {
  updateCandidateStatusStage,
  createNote,
  deleteNote,
  ApiError,
  STATUS_LABELS,
  STAGE_LABELS,
} from '@/lib/api';
import type {
  CandidateStatus,
  CandidateStage,
  SchemaErrorEntry,
  UpdateCandidateStatusStageInput,
} from '@/lib/api';

function mapApiError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.kind === 'business') {
      return err.message;
    }
    if (err.kind === 'schema') {
      const entries = err.details as SchemaErrorEntry[] | undefined;
      return entries?.[0]?.msg ?? 'Validation failed.';
    }
    return 'Network error. Please try again.';
  }
  return 'An unexpected error occurred.';
}

/** Result returned to the Client Component after a status/stage update. */
export interface UpdateCandidateActionResult {
  success: boolean;
  /** User-facing error message on failure; undefined on success. */
  error?: string;
}

/**
 * Server Action: update a candidate's status and/or stage.
 *
 * Validates that any provided fields are members of the corresponding
 * union (via `value in LABELS`, with the labels map typed as
 * Record<Union, string> serving as the source of truth).
 *
 * On success, revalidates the detail page and the list page (the list
 * row displays the badge too). On failure, returns a typed error
 * message: business-rule errors carry the backend's exact message;
 * schema errors surface the first validation issue.
 */
export async function updateCandidateAction(
  candidateId: string,
  patch: { status?: string; stage?: string },
): Promise<UpdateCandidateActionResult> {
  const cleanPatch: UpdateCandidateStatusStageInput = {};

  if (patch.status !== undefined) {
    if (!(patch.status in STATUS_LABELS)) {
      return { success: false, error: `Invalid status: ${patch.status}` };
    }
    // Safe: just verified the key exists in STATUS_LABELS, which is
    // typed as Record<CandidateStatus, string>.
    cleanPatch.status = patch.status as CandidateStatus;
  }

  if (patch.stage !== undefined) {
    if (!(patch.stage in STAGE_LABELS)) {
      return { success: false, error: `Invalid stage: ${patch.stage}` };
    }
    cleanPatch.stage = patch.stage as CandidateStage;
  }

  if (Object.keys(cleanPatch).length === 0) {
    return { success: false, error: 'No valid fields to update.' };
  }

  try {
    await updateCandidateStatusStage(candidateId, cleanPatch);
  } catch (err) {
    return { success: false, error: mapApiError(err) };
  }
  revalidatePath(`/candidates/${candidateId}`);
  revalidatePath('/');
  return { success: true };
}

/** Result returned to the Client Component after a note mutation. */
export interface NoteActionResult {
  success: boolean;
  /** User-facing error message on failure; undefined on success. */
  error?: string;
}

/**
 * Server Action: create a note on a candidate.
 *
 * Trims and length-caps content server-side (5000 chars). On success,
 * revalidates the detail page and the list page (notes_count in sync).
 */
export async function createNoteAction(
  candidateId: string,
  content: string,
): Promise<NoteActionResult> {
  const trimmed = content.trim();
  if (!trimmed) {
    return { success: false, error: 'Note content cannot be empty.' };
  }
  if (trimmed.length > 5000) {
    return { success: false, error: 'Note is too long (max 5000 characters).' };
  }

  try {
    await createNote(candidateId, trimmed);
  } catch (err) {
    return { success: false, error: mapApiError(err) };
  }
  revalidatePath(`/candidates/${candidateId}`);
  revalidatePath('/');
  return { success: true };
}

/**
 * Server Action: delete a note from a candidate.
 *
 * On success, revalidates the detail page and the list page so
 * notes_count refreshes.
 */
export async function deleteNoteAction(
  candidateId: string,
  noteId: string,
): Promise<NoteActionResult> {
  try {
    await deleteNote(candidateId, noteId);
  } catch (err) {
    return { success: false, error: mapApiError(err) };
  }
  revalidatePath(`/candidates/${candidateId}`);
  revalidatePath('/');
  return { success: true };
}
