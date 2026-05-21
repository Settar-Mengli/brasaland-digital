'use client';

import { useOptimistic, useState, useTransition } from 'react';
import { STATUS_LABELS, STAGE_LABELS } from '@/lib/api';
import type { CandidateStatus, CandidateStage } from '@/lib/api';
import { updateCandidateAction } from '../_actions';

interface StatusStageEditorProps {
  candidateId: string;
  currentStatus: CandidateStatus;
  currentStage: CandidateStage;
}

/**
 * Client Component for editing a candidate's status and stage.
 *
 * Each dropdown auto-submits on change via a Server Action. Optimistic
 * UI shows the new value immediately; if the action fails, the optimistic
 * state reverts (because the underlying props don't change) and the
 * error message is displayed inline.
 */
export default function StatusStageEditor({
  candidateId,
  currentStatus,
  currentStage,
}: StatusStageEditorProps) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const [optimisticStatus, setOptimisticStatus] = useOptimistic(currentStatus);
  const [optimisticStage, setOptimisticStage] = useOptimistic(currentStage);

  function handleStatusChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const newStatus = event.target.value;
    if (newStatus === currentStatus) return;
    setError(null);
    startTransition(async () => {
      setOptimisticStatus(newStatus as CandidateStatus);
      const result = await updateCandidateAction(candidateId, { status: newStatus });
      if (!result.success) {
        setError(result.error ?? 'Could not update status.');
      }
    });
  }

  function handleStageChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const newStage = event.target.value;
    if (newStage === currentStage) return;
    setError(null);
    startTransition(async () => {
      setOptimisticStage(newStage as CandidateStage);
      const result = await updateCandidateAction(candidateId, { stage: newStage });
      if (!result.success) {
        setError(result.error ?? 'Could not update stage.');
      }
    });
  }

  const selectClass =
    'border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md text-brasaland-charcoal focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:border-brasaland-ember disabled:opacity-60';

  return (
    <section
      aria-labelledby="manage-heading"
      className="rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream/40 p-6 mb-6"
    >
      <h2
        id="manage-heading"
        className="font-display text-xl font-semibold text-brasaland-charcoal mb-4"
      >
        Manage pipeline state
      </h2>

      <div className="flex flex-col gap-4 md:flex-row md:gap-6">
        <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal md:flex-1">
          Status
          <select
            value={optimisticStatus}
            onChange={handleStatusChange}
            disabled={isPending}
            className={selectClass}
          >
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal md:flex-1">
          Stage
          <select
            value={optimisticStage}
            onChange={handleStageChange}
            disabled={isPending}
            className={selectClass}
          >
            {Object.entries(STAGE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {isPending && (
        <p className="mt-3 text-sm text-brasaland-charcoal/60 animate-pulse" role="status">
          Updating…
        </p>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm text-brasaland-error font-medium">
          {error}
        </p>
      )}
    </section>
  );
}
