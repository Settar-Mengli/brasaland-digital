'use server';

import { revalidatePath } from 'next/cache';
import { updateCandidateStatusStage, ApiError, STATUS_LABELS, STAGE_LABELS } from '@/lib/api';
import type {
  CandidateStatus,
  CandidateStage,
  SchemaErrorEntry,
  UpdateCandidateStatusStageInput,
} from '@/lib/api';

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
    revalidatePath(`/candidates/${candidateId}`);
    revalidatePath('/');
    return { success: true };
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.kind === 'business') {
        return { success: false, error: err.message };
      }
      if (err.kind === 'schema') {
        const entries = err.details as SchemaErrorEntry[] | undefined;
        const firstMsg = entries?.[0]?.msg ?? 'Validation failed.';
        return { success: false, error: firstMsg };
      }
      return { success: false, error: 'Network error. Please try again.' };
    }
    return { success: false, error: 'An unexpected error occurred.' };
  }
}
