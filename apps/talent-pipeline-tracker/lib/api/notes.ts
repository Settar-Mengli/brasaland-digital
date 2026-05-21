/**
 * Endpoint wrappers for the nested `/records/{id}/notes` resource.
 */

import type { CollectionResponse, Note } from './types';
import { apiFetch } from './client';

/** List all notes attached to a candidate. Returns a wrapped envelope. */
export async function listNotes(candidateId: string): Promise<CollectionResponse<Note>> {
  return apiFetch<CollectionResponse<Note>>(`/records/${encodeURIComponent(candidateId)}/notes`);
}

/** Create a new note on a candidate. */
export async function createNote(candidateId: string, content: string): Promise<Note> {
  return apiFetch<Note>(`/records/${encodeURIComponent(candidateId)}/notes`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

/** Delete a note. Returns once the server confirms (204). */
export async function deleteNote(candidateId: string, noteId: string): Promise<void> {
  await apiFetch<void>(
    `/records/${encodeURIComponent(candidateId)}/notes/${encodeURIComponent(noteId)}`,
    { method: 'DELETE' },
  );
}
