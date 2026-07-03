'use client';

import { useCallback, useEffect, useState } from 'react';

import { formInputClassName } from '@/app/_components/FormField';
import {
  CATEGORY_LABELS,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  type Incident,
  type IncidentBranch,
  type IncidentCategory,
  type IncidentListFilters,
  type IncidentOrigin,
  type IncidentStatus,
} from '@/lib/incident-types';
import {
  formatIncidentTimestamp,
  getEmptyIncidentsMessage,
  STATUS_BADGE_CLASSES,
} from '@/lib/incident-display';
import { getIncidents, updateStatus } from '@/lib/incidents';
import {
  canUpdateIncidentStatus,
  getStatusSelectOptions,
  resolveStatusAfterUpdate,
  STATUS_UPDATE_FAILURE_MESSAGE,
} from '@/lib/incident-status-control';

type FilterState = {
  status: string;
  origin: string;
  branch: string;
  category: string;
};

const EMPTY_FILTERS: FilterState = {
  status: '',
  origin: '',
  branch: '',
  category: '',
};

const BRANCH_FILTER_ORDER: readonly IncidentBranch[] = [
  'Central',
  'COL-01',
  'COL-02',
  'COL-03',
  'COL-04',
  'COL-05',
  'COL-06',
  'COL-07',
  'COL-08',
  'COL-09',
  'COL-10',
  'FLA-01',
  'FLA-02',
  'FLA-03',
  'FLA-04',
];

function buildApiFilters(filters: FilterState): IncidentListFilters {
  const apiFilters: IncidentListFilters = {};

  if (filters.status) {
    apiFilters.status = filters.status as IncidentStatus;
  }
  if (filters.origin) {
    apiFilters.origin = filters.origin as IncidentOrigin;
  }
  if (filters.branch) {
    apiFilters.branch = filters.branch as IncidentBranch;
  }
  if (filters.category) {
    apiFilters.category = filters.category as IncidentCategory;
  }

  return apiFilters;
}

function filtersAreActive(filters: FilterState): boolean {
  return Boolean(filters.status || filters.origin || filters.branch || filters.category);
}

function StatusBadge({ status }: { status: IncidentStatus }) {
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE_CLASSES[status]}`}
    >
      {status}
    </span>
  );
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [lastGoodIncidents, setLastGoodIncidents] = useState<Incident[]>([]);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [statusUpdateError, setStatusUpdateError] = useState<string | null>(null);
  const [updatingIncidentId, setUpdatingIncidentId] = useState<number | null>(null);

  const inputClassName = formInputClassName();
  const filtersActive = filtersAreActive(filters);
  const displayIncidents = error && lastGoodIncidents.length > 0 ? lastGoodIncidents : incidents;

  const loadIncidents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getIncidents(buildApiFilters(filters));
      setIncidents(data);
      setLastGoodIncidents(data);
      setHasLoadedOnce(true);
    } catch (loadError) {
      const message =
        loadError instanceof Error ? loadError.message : 'Unable to load incidents right now.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadIncidents();
  }, [loadIncidents]);

  function updateFilter<K extends keyof FilterState>(key: K, value: FilterState[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
    setStatusUpdateError(null);
  }

  async function handleStatusChange(incident: Incident, nextStatus: IncidentStatus) {
    if (nextStatus === incident.status) {
      return;
    }

    const previousStatus = incident.status;
    setStatusUpdateError(null);
    setUpdatingIncidentId(incident.id);

    setIncidents((current) =>
      current.map((row) => (row.id === incident.id ? { ...row, status: nextStatus } : row)),
    );

    try {
      const updated = await updateStatus(incident.id, nextStatus);
      const resolvedStatus = resolveStatusAfterUpdate(
        previousStatus,
        nextStatus,
        true,
        updated.status,
      );

      setIncidents((current) =>
        current.map((row) => (row.id === incident.id ? { ...row, status: resolvedStatus } : row)),
      );
      setLastGoodIncidents((current) =>
        current.map((row) => (row.id === incident.id ? { ...row, status: resolvedStatus } : row)),
      );
    } catch {
      const revertedStatus = resolveStatusAfterUpdate(previousStatus, nextStatus, false);

      setIncidents((current) =>
        current.map((row) => (row.id === incident.id ? { ...row, status: revertedStatus } : row)),
      );
      setStatusUpdateError(STATUS_UPDATE_FAILURE_MESSAGE);
    } finally {
      setUpdatingIncidentId(null);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Incident List</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Filter incidents and update status inline across Brasaland locations.
        </p>
      </div>

      <section
        aria-labelledby="incidents-heading"
        className="border border-brasaland-charcoal/10 rounded-xl p-6 bg-white shadow-sm"
      >
        <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
          <h2 id="incidents-heading" className="font-semibold text-xl">
            Incidents
          </h2>
          <p className="text-sm text-brasaland-charcoal/60" role="status">
            {loading
              ? 'Loading incidents…'
              : `${displayIncidents.length} incident${displayIncidents.length === 1 ? '' : 's'}`}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-4">
          <div>
            <label htmlFor="filter-status" className="block text-sm font-medium mb-1">
              Status
            </label>
            <select
              id="filter-status"
              value={filters.status}
              onChange={(event) => updateFilter('status', event.target.value)}
              className={inputClassName}
            >
              <option value="">All</option>
              {INCIDENT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="filter-origin" className="block text-sm font-medium mb-1">
              Origin
            </label>
            <select
              id="filter-origin"
              value={filters.origin}
              onChange={(event) => updateFilter('origin', event.target.value)}
              className={inputClassName}
            >
              <option value="">All</option>
              {INCIDENT_ORIGINS.map((origin) => (
                <option key={origin} value={origin}>
                  {origin}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="filter-branch" className="block text-sm font-medium mb-1">
              Branch
            </label>
            <select
              id="filter-branch"
              value={filters.branch}
              onChange={(event) => updateFilter('branch', event.target.value)}
              className={inputClassName}
            >
              <option value="">All</option>
              {BRANCH_FILTER_ORDER.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="filter-category" className="block text-sm font-medium mb-1">
              Category
            </label>
            <select
              id="filter-category"
              value={filters.category}
              onChange={(event) => updateFilter('category', event.target.value)}
              className={inputClassName}
            >
              <option value="">All</option>
              {INCIDENT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {CATEGORY_LABELS[category]}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error ? (
          <div
            role="alert"
            className="mb-4 flex flex-wrap items-center gap-3 text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => void loadIncidents()}
              className="px-3 py-1 rounded-md border border-brasaland-error/30 bg-white text-brasaland-error font-medium hover:bg-brasaland-error/5"
            >
              Retry
            </button>
          </div>
        ) : null}

        {statusUpdateError ? (
          <p
            role="alert"
            className="mb-4 text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            {statusUpdateError}
          </p>
        ) : null}

        {loading ? (
          <p className="text-sm text-brasaland-charcoal/60">Loading incidents…</p>
        ) : displayIncidents.length === 0 ? (
          <p className="text-sm text-brasaland-charcoal/60">
            {getEmptyIncidentsMessage(filtersActive, hasLoadedOnce)}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse" aria-labelledby="incidents-heading">
              <thead className="bg-brasaland-charcoal/5">
                <tr>
                  <th scope="col" className="text-left p-3 font-semibold">
                    ID
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Title
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Category
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Origin
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Branch
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Status
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Created
                  </th>
                  <th scope="col" className="text-left p-3 font-semibold">
                    Update status
                  </th>
                </tr>
              </thead>
              <tbody>
                {displayIncidents.map((incident) => {
                  const selectOptions = getStatusSelectOptions(incident.status);
                  const statusEditable = canUpdateIncidentStatus(incident.status);

                  return (
                    <tr key={incident.id} className="border-t border-brasaland-charcoal/10">
                      <td className="p-3 tabular-nums">{incident.id}</td>
                      <td className="p-3">
                        <div className="font-medium">{incident.title}</div>
                        <p className="text-brasaland-charcoal/60 mt-1">{incident.description}</p>
                      </td>
                      <td className="p-3">{CATEGORY_LABELS[incident.category]}</td>
                      <td className="p-3">{incident.origin}</td>
                      <td className="p-3">{incident.branch}</td>
                      <td className="p-3">
                        <StatusBadge status={incident.status} />
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        {formatIncidentTimestamp(incident.created_at)}
                      </td>
                      <td className="p-3">
                        <select
                          aria-label={`Update status for ${incident.title}`}
                          value={incident.status}
                          disabled={!statusEditable || updatingIncidentId === incident.id}
                          onChange={(event) =>
                            void handleStatusChange(incident, event.target.value as IncidentStatus)
                          }
                          className={inputClassName}
                        >
                          {selectOptions.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
