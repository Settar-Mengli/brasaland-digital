'use client';

import { useOptimistic, useState, useTransition } from 'react';
import type { Note } from '@/lib/api';
import { createNoteAction, deleteNoteAction } from '../_actions';

interface NotesThreadProps {
  candidateId: string;
  /** Notes fetched server-side; passed in as the initial render state. */
  initialNotes: Note[];
}

/** Discriminated action for the optimistic notes reducer. */
type OptimisticAction = { type: 'add'; note: Note } | { type: 'delete'; id: string };

const noteDateFormatter = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

/**
 * Notes thread: read + add + delete with optimistic UI.
 *
 * Uses useOptimistic with a reducer so add/delete are immediately
 * visible. On Server Action failure, the optimistic state auto-reverts
 * (because the underlying initialNotes prop didn't change) and an
 * inline error message is displayed.
 */
export default function NotesThread({ candidateId, initialNotes }: NotesThreadProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);

  const [optimisticNotes, mutateOptimistic] = useOptimistic(
    initialNotes,
    (current: Note[], action: OptimisticAction): Note[] => {
      if (action.type === 'add') return [action.note, ...current];
      if (action.type === 'delete') return current.filter((n) => n.id !== action.id);
      return current;
    },
  );

  function handleAdd(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content) return;
    setError(null);
    startTransition(async () => {
      // Temporary optimistic note with a placeholder id; replaced when
      // the server re-renders with revalidatePath.
      const tempNote: Note = {
        id: `temp-${Date.now()}`,
        record_id: candidateId,
        content,
        created_at: new Date().toISOString(),
      };
      mutateOptimistic({ type: 'add', note: tempNote });
      const result = await createNoteAction(candidateId, content);
      if (result.success) {
        setDraft('');
      } else {
        setError(result.error ?? 'Could not add note.');
      }
    });
  }

  function handleDelete(noteId: string) {
    setError(null);
    setConfirmingDeleteId(null);
    startTransition(async () => {
      mutateOptimistic({ type: 'delete', id: noteId });
      const result = await deleteNoteAction(candidateId, noteId);
      if (!result.success) {
        setError(result.error ?? 'Could not delete note.');
      }
    });
  }

  const inputClass =
    'w-full border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md text-brasaland-charcoal focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:border-brasaland-ember disabled:opacity-60';

  const primaryButtonClass =
    'px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-ivory disabled:opacity-60 transition-colors';

  const secondaryButtonClass =
    'px-3 py-1.5 rounded-md border border-brasaland-charcoal/20 text-sm text-brasaland-charcoal hover:bg-brasaland-cream focus:outline-none focus:ring-2 focus:ring-brasaland-ember disabled:opacity-60 transition-colors';

  const destructiveButtonClass =
    'px-3 py-1.5 rounded-md bg-brasaland-error text-white text-sm font-medium hover:bg-brasaland-error/90 focus:outline-none focus:ring-2 focus:ring-brasaland-error focus:ring-offset-2 focus:ring-offset-brasaland-ivory disabled:opacity-60 transition-colors';

  return (
    <section
      aria-labelledby="notes-heading"
      className="mt-6 rounded-lg border border-brasaland-charcoal/10 bg-brasaland-ivory p-6"
    >
      <h2
        id="notes-heading"
        className="font-display text-xl font-semibold text-brasaland-charcoal mb-4"
      >
        Notes
      </h2>

      <form onSubmit={handleAdd} className="mb-6">
        <label
          htmlFor="note-content"
          className="block text-sm font-medium text-brasaland-charcoal mb-1"
        >
          Add a note
        </label>
        <textarea
          id="note-content"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={isPending}
          rows={3}
          maxLength={5000}
          placeholder="Share an observation about this candidate…"
          className={inputClass}
        />
        <div className="mt-2 flex items-center justify-between">
          <span className="text-xs text-brasaland-charcoal/60">{draft.length} / 5000</span>
          <button
            type="submit"
            disabled={isPending || draft.trim().length === 0}
            className={primaryButtonClass}
          >
            {isPending ? 'Saving…' : 'Add note'}
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" className="mb-4 text-sm text-brasaland-error font-medium">
          {error}
        </p>
      )}

      {optimisticNotes.length === 0 ? (
        <p className="text-brasaland-charcoal/60 italic">No notes yet. Add the first one above.</p>
      ) : (
        <ul className="space-y-3" aria-label="Notes list">
          {optimisticNotes.map((note) => (
            <li
              key={note.id}
              className="rounded-md border border-brasaland-charcoal/10 bg-brasaland-cream/30 p-4"
            >
              <p className="text-brasaland-charcoal whitespace-pre-wrap break-words">
                {note.content}
              </p>
              <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
                <time dateTime={note.created_at} className="text-xs text-brasaland-charcoal/60">
                  {noteDateFormatter.format(new Date(note.created_at))}
                </time>
                {confirmingDeleteId === note.id ? (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-brasaland-charcoal/80">Delete this note?</span>
                    <button
                      type="button"
                      onClick={() => handleDelete(note.id)}
                      disabled={isPending}
                      className={destructiveButtonClass}
                    >
                      Yes, delete
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfirmingDeleteId(null)}
                      disabled={isPending}
                      className={secondaryButtonClass}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setConfirmingDeleteId(note.id)}
                    disabled={isPending}
                    className={secondaryButtonClass}
                  >
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
