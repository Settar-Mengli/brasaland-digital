'use client';

import { useCallback, useEffect, useState } from 'react';

import {
  CATEGORY_LABELS,
  type IncidentBranch,
  type IncidentCategory,
  type IncidentOrigin,
  type IncidentStatus,
  type IncidentSummary,
} from '@/lib/incident-types';
import { sortedCountEntries } from '@/lib/incident-display';
import { getSummary } from '@/lib/incidents';

type SummaryMetricCardProps = {
  title: string;
  entries: Array<{ key: string; count: number }>;
  formatLabel?: (key: string) => string;
};

function SummaryMetricCard({ title, entries, formatLabel }: SummaryMetricCardProps) {
  return (
    <div className="rounded-xl border border-brasaland-charcoal/10 bg-brasaland-cream p-4">
      <h3 className="font-semibold mb-3">{title}</h3>
      {entries.length === 0 ? (
        <p className="text-sm text-brasaland-charcoal/60">None</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {entries.map((entry) => (
            <li key={entry.key} className="flex items-center justify-between gap-3">
              <span>{formatLabel ? formatLabel(entry.key) : entry.key}</span>
              <strong className="tabular-nums">{entry.count}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function SummaryPage() {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getSummary();
      setSummary(data);
    } catch (loadError) {
      const message =
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load summary metrics right now.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Summary</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1" role="status">
          {loading
            ? 'Loading summary…'
            : summary
              ? `${summary.total} incidents tracked`
              : 'Summary unavailable'}
        </p>
      </div>

      <section
        aria-labelledby="summary-heading"
        className="border border-brasaland-charcoal/10 rounded-xl p-6 bg-white shadow-sm"
      >
        <h2 id="summary-heading" className="font-semibold text-xl mb-4">
          Chain-wide metrics
        </h2>

        {loading ? (
          <p className="text-sm text-brasaland-charcoal/60">Loading summary metrics…</p>
        ) : null}

        {error ? (
          <div
            role="alert"
            className="flex flex-wrap items-center gap-3 text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => void loadSummary()}
              className="px-3 py-1 rounded-md border border-brasaland-error/30 bg-white text-brasaland-error font-medium hover:bg-brasaland-error/5"
            >
              Retry
            </button>
          </div>
        ) : null}

        {!loading && !error && summary ? (
          summary.total === 0 ? (
            <p className="text-sm text-brasaland-charcoal/60">
              No incident data yet. Summary metrics will appear after incidents are registered.
            </p>
          ) : (
            <div className="space-y-6">
              <div className="rounded-xl border border-brasaland-charcoal/10 bg-brasaland-cream p-4">
                <h3 className="font-semibold mb-2">Total incidents</h3>
                <p className="text-3xl font-bold text-brasaland-ember tabular-nums">
                  {summary.total}
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <SummaryMetricCard
                  title="By status"
                  entries={sortedCountEntries<IncidentStatus>(summary.by_status)}
                />
                <SummaryMetricCard
                  title="By category"
                  entries={sortedCountEntries<IncidentCategory>(summary.by_category)}
                  formatLabel={(key) => CATEGORY_LABELS[key as IncidentCategory] ?? key}
                />
                <SummaryMetricCard
                  title="By origin"
                  entries={sortedCountEntries<IncidentOrigin>(summary.by_origin)}
                />
                <SummaryMetricCard
                  title="By branch"
                  entries={sortedCountEntries<IncidentBranch>(summary.by_branch)}
                />
              </div>
            </div>
          )
        ) : null}
      </section>
    </div>
  );
}
