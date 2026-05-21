import Link from 'next/link';
import { getCandidate, STATUS_LABELS, STAGE_LABELS } from '@/lib/api';
import type { CandidateStatus } from '@/lib/api';

/**
 * Force dynamic rendering — candidate data must reflect the live state
 * on every request, not stale build-time data.
 */
export const dynamic = 'force-dynamic';

const BADGE_BASE = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium';

const STATUS_BADGE_CLASSES: Record<CandidateStatus, string> = {
  received: 'bg-brasaland-charcoal/10 text-brasaland-charcoal/80',
  in_progress: 'bg-brasaland-ember/10 text-brasaland-ember',
  selected: 'bg-brasaland-success/10 text-brasaland-success',
  discarded: 'bg-brasaland-error/10 text-brasaland-error',
};

const STAGE_BADGE_CLASS =
  'bg-brasaland-charcoal/5 text-brasaland-charcoal/80 ring-1 ring-brasaland-charcoal/10';

const dateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

/** Read-only detail view for a single candidate. */
export default async function CandidateDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const candidate = await getCandidate(id);

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-4xl">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-brasaland-charcoal/70 hover:text-brasaland-charcoal mb-6 focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded"
        >
          ← Back to candidates
        </Link>

        <header className="mb-8">
          <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-ember">
            Candidate
          </p>
          <h1 className="mt-2 font-display text-4xl font-bold text-brasaland-charcoal">
            {candidate.full_name}
          </h1>
          <p className="mt-2 text-lg text-brasaland-charcoal/80">{candidate.position}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className={`${BADGE_BASE} ${STATUS_BADGE_CLASSES[candidate.status]}`}>
              {STATUS_LABELS[candidate.status]}
            </span>
            <span className={`${BADGE_BASE} ${STAGE_BADGE_CLASS}`}>
              {STAGE_LABELS[candidate.stage]}
            </span>
          </div>
        </header>

        <section
          aria-labelledby="info-heading"
          className="rounded-lg border border-brasaland-charcoal/10 bg-brasaland-ivory p-6"
        >
          <h2 id="info-heading" className="sr-only">
            Candidate details
          </h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Email</dt>
              <dd className="mt-1 text-brasaland-charcoal break-words">{candidate.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Phone</dt>
              <dd className="mt-1 text-brasaland-charcoal break-words">{candidate.phone}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Experience</dt>
              <dd className="mt-1 text-brasaland-charcoal">
                {candidate.experience_years} {candidate.experience_years === 1 ? 'year' : 'years'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Notes</dt>
              <dd className="mt-1 text-brasaland-charcoal">{candidate.notes_count ?? 0}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Applied</dt>
              <dd className="mt-1 text-brasaland-charcoal">
                {dateTimeFormatter.format(new Date(candidate.applied_at))}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-brasaland-charcoal/60">Last updated</dt>
              <dd className="mt-1 text-brasaland-charcoal">
                {dateTimeFormatter.format(new Date(candidate.updated_at))}
              </dd>
            </div>

            {candidate.linkedin_url && (
              <div className="md:col-span-2">
                <dt className="text-sm font-medium text-brasaland-charcoal/60">LinkedIn</dt>
                <dd className="mt-1">
                  <a
                    href={candidate.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded break-all"
                  >
                    {candidate.linkedin_url} ↗
                  </a>
                </dd>
              </div>
            )}
            {candidate.cv_url && (
              <div className="md:col-span-2">
                <dt className="text-sm font-medium text-brasaland-charcoal/60">CV</dt>
                <dd className="mt-1">
                  <a
                    href={candidate.cv_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded break-all"
                  >
                    {candidate.cv_url} ↗
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </section>
      </div>
    </main>
  );
}
