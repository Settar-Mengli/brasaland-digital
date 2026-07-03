import type { IncidentStatus } from './incident-types';

export const STATUS_BADGE_CLASSES: Record<IncidentStatus, string> = {
  open: 'bg-amber-100 text-amber-800',
  in_progress: 'bg-sky-100 text-sky-800',
  resolved: 'bg-brasaland-success/10 text-brasaland-success',
  discarded: 'bg-brasaland-charcoal/10 text-brasaland-charcoal/70',
};

export function formatIncidentTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export function getEmptyIncidentsMessage(filtersActive: boolean, hasLoadedOnce: boolean): string {
  if (!hasLoadedOnce) {
    return 'No incidents recorded yet.';
  }

  if (filtersActive) {
    return 'No incidents match the current filters.';
  }

  return 'No incidents recorded yet.';
}
