import Link from 'next/link';

interface PaginationProps {
  /** Current page (1-indexed). */
  current: number;
  /** Total number of records across all pages. */
  total: number;
  /** Records per page. */
  limit: number;
  /** Current URL params (without `page`) to preserve on page change. */
  baseParams: URLSearchParams;
}

/**
 * Server-rendered pagination control. Renders nothing when there is only
 * one page; otherwise renders Prev / Page X of Y / Next as Link components.
 * Disabled controls render as semantic spans rather than non-navigable links.
 */
export default function Pagination({ current, total, limit, baseParams }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  if (totalPages <= 1) return null;

  function pageHref(page: number): string {
    const next = new URLSearchParams(baseParams);
    if (page > 1) {
      next.set('page', String(page));
    } else {
      next.delete('page');
    }
    const query = next.toString();
    return query ? `/?${query}` : '/';
  }

  const hasPrev = current > 1;
  const hasNext = current < totalPages;

  const linkClass =
    'px-3 py-2 rounded-md border border-brasaland-charcoal/20 bg-brasaland-ivory text-brasaland-charcoal text-sm font-medium hover:bg-brasaland-cream focus:outline-none focus:ring-2 focus:ring-brasaland-ember transition-colors';
  const disabledClass =
    'px-3 py-2 rounded-md border border-brasaland-charcoal/10 bg-brasaland-ivory/50 text-brasaland-charcoal/40 text-sm font-medium cursor-not-allowed';

  return (
    <nav aria-label="Candidate list pagination" className="mt-6 flex items-center justify-between">
      {hasPrev ? (
        <Link href={pageHref(current - 1)} className={linkClass}>
          ← Previous
        </Link>
      ) : (
        <span aria-disabled="true" className={disabledClass}>
          ← Previous
        </span>
      )}

      <span className="text-sm text-brasaland-charcoal/70">
        Page <strong className="font-semibold text-brasaland-charcoal">{current}</strong> of{' '}
        <strong className="font-semibold text-brasaland-charcoal">{totalPages}</strong>
      </span>

      {hasNext ? (
        <Link href={pageHref(current + 1)} className={linkClass}>
          Next →
        </Link>
      ) : (
        <span aria-disabled="true" className={disabledClass}>
          Next →
        </span>
      )}
    </nav>
  );
}
