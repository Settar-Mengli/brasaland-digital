import type { IncidentStatus } from './incident-types';
import { getAllowedNextStatuses } from './incident-types';

export function getStatusSelectOptions(current: IncidentStatus): IncidentStatus[] {
  const allowedNext = getAllowedNextStatuses(current);
  if (allowedNext.length === 0) {
    return [current];
  }
  return [current, ...allowedNext];
}

export function canUpdateIncidentStatus(current: IncidentStatus): boolean {
  return getAllowedNextStatuses(current).length > 0;
}

export function resolveStatusAfterUpdate(
  previousStatus: IncidentStatus,
  attemptedStatus: IncidentStatus,
  succeeded: boolean,
  confirmedStatus?: IncidentStatus,
): IncidentStatus {
  if (!succeeded) {
    return previousStatus;
  }

  if (confirmedStatus !== undefined) {
    return confirmedStatus;
  }

  return attemptedStatus;
}

export const STATUS_UPDATE_FAILURE_MESSAGE =
  'That status change is not allowed. The previous status has been restored.';
