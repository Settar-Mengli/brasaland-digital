import Link from 'next/link';
import { listCandidates, STATUS_LABELS, STAGE_LABELS } from '@/lib/api';
import type { CandidateStatus, CandidateStage } from '@/lib/api';
import FilterBar from './_components/FilterBar';
import Pagination from './_components/Pagination';

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

/**
 * Type guard: is the raw URL param value a valid CandidateStatus?
 * Uses STATUS_LABELS as the source of truth — TypeScript enforces that
 * the labels map has exactly the union's keys.
 */
function isValidStatus(value: string): value is CandidateStatus {
  return value in STATUS_LABELS;
}

/** Type guard: is the raw URL param value a valid CandidateStage? */
function isValidStage(value: string): value is CandidateStage {
  return value in STAGE_LABELS;
}

/**
 * Parse a 1-indexed page number from a raw URL param.
 * Falls back to 1 for missing, non-numeric, or non-positive values.
 */
function parsePage(raw: string | undefined): number {
  if (!raw) return 1;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n >= 1 ? n : 1;
}

const PAGE_SIZE = 20;

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{
    status?: string;
    stage?: string;
    search?: string;
    page?: string;
  }>;
}) {
  const params = await searchParams;

  const status = params.status && isValidStatus(params.status) ? params.status : undefined;
  const stage = params.stage && isValidStage(params.stage) ? params.stage : undefined;
  const search = params.search?.trim() || undefined;
  const page = parsePage(params.page);

  const result = await listCandidates({
    status,
    stage,
    search,
    page,
    limit: PAGE_SIZE,
  });

  // Build base params (without `page`) for the Pagination component.
  const baseParams = new URLSearchParams();
  if (status) baseParams.set('status', status);
  if (stage) baseParams.set('stage', stage);
  if (search) baseParams.set('search', search);

  // Force FilterBar to remount when URL changes so defaultValue picks up new values.
  const filterKey = baseParams.toString();

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-6xl">
        {/* Page header */}
        <header className="mb-8">
          <h1 className="font-display text-4xl font-bold text-brasaland-charcoal">Candidates</h1>
          <p className="mt-2 text-brasaland-charcoal/70">Brasaland talent pipeline overview.</p>
        </header>

        <FilterBar key={filterKey} defaults={{ status, stage, search }} />

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
                    <td className="px-4 py-3 font-medium">
                      <Link
                        href={`/candidates/${candidate.id}`}
                        className="text-brasaland-charcoal hover:text-brasaland-ember focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded transition-colors"
                      >
                        {candidate.full_name}
                      </Link>
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

        <Pagination current={page} total={result.total} limit={PAGE_SIZE} baseParams={baseParams} />
      </div>
    </main>
  );
}
