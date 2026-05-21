import { listCandidates, STATUS_LABELS, STAGE_LABELS } from '@/lib/api';
import type { CandidateStatus } from '@/lib/api';

/**
 * Force dynamic rendering — the candidate list must reflect live state on
 * every request, not stale data from build-time pre-render.
 */
export const dynamic = 'force-dynamic';

const BADGE_BASE = 'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium';

const STATUS_BADGE_CLASSES: Record<CandidateStatus, string> = {
  received: 'bg-brasaland-charcoal/10 text-brasaland-charcoal/80',
  in_progress: 'bg-brasaland-ember/10 text-brasaland-ember',
  selected: 'bg-brasaland-success/10 text-brasaland-success',
  discarded: 'bg-brasaland-error/10 text-brasaland-error',
};

const STAGE_BADGE_CLASS =
  'bg-brasaland-charcoal/5 text-brasaland-charcoal/80 ring-1 ring-brasaland-charcoal/10';

const dateFormatter = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' });

export default async function HomePage() {
  const result = await listCandidates({ limit: 20 });

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-6xl">
        {/* Page header */}
        <header className="mb-8">
          <h1 className="font-display text-4xl font-bold text-brasaland-charcoal">Candidates</h1>
          <p className="mt-2 text-brasaland-charcoal/70">Brasaland talent pipeline overview.</p>
        </header>

        {/* Filter bar — disabled, static */}
        <section
          aria-labelledby="filters-heading"
          className="rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream/40 p-4 mb-6"
        >
          <h2 id="filters-heading" className="sr-only">
            Filter candidates
          </h2>
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
              Status
              <select
                disabled
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              >
                <option value="">All statuses</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal">
              Stage
              <select
                disabled
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              >
                <option value="">All stages</option>
                {Object.entries(STAGE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-brasaland-charcoal md:flex-1">
              Search
              <input
                type="search"
                disabled
                placeholder="Name, email, or position"
                className="border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 rounded-md disabled:opacity-60"
              />
            </label>
          </div>
          <p className="mt-3 text-xs text-brasaland-charcoal/60">
            Filters become interactive in a later commit.
          </p>
        </section>

        <p className="mb-3 text-sm text-brasaland-charcoal/70">
          Showing{' '}
          <strong className="font-semibold text-brasaland-charcoal">{result.data.length}</strong> of{' '}
          <strong className="font-semibold text-brasaland-charcoal">{result.total}</strong>{' '}
          candidates.
        </p>

        {/* Candidate table */}
        <section
          aria-labelledby="candidates-heading"
          className="overflow-x-auto rounded-lg border border-brasaland-charcoal/10 bg-brasaland-ivory"
        >
          <h2 id="candidates-heading" className="sr-only">
            Candidate list
          </h2>
          <table className="w-full text-left text-sm">
            <thead className="bg-brasaland-cream/50 text-brasaland-charcoal">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Name
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Position
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Experience
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Stage
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Notes
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Applied
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brasaland-charcoal/5">
              {result.data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-brasaland-charcoal/60">
                    No candidates match the current filters.
                  </td>
                </tr>
              ) : (
                result.data.map((candidate) => (
                  <tr key={candidate.id}>
                    <td className="px-4 py-3 font-medium text-brasaland-charcoal">
                      {candidate.full_name}
                    </td>
                    <td className="px-4 py-3 text-brasaland-charcoal/80">{candidate.position}</td>
                    <td className="px-4 py-3 text-brasaland-charcoal/80">
                      {candidate.experience_years}y
                    </td>
                    <td className="px-4 py-3">
                      <span className={`${BADGE_BASE} ${STATUS_BADGE_CLASSES[candidate.status]}`}>
                        {STATUS_LABELS[candidate.status]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`${BADGE_BASE} ${STAGE_BADGE_CLASS}`}>
                        {STAGE_LABELS[candidate.stage]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-brasaland-charcoal/80">
                      {candidate.notes_count ?? 0}
                    </td>
                    <td className="px-4 py-3 text-brasaland-charcoal/80">
                      {dateFormatter.format(new Date(candidate.applied_at))}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </section>
      </div>
    </main>
  );
}
