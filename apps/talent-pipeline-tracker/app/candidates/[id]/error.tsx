'use client';

import Link from 'next/link';
import { useEffect } from 'react';

/**
 * Route-level error boundary for the candidate detail page.
 * Offers retry (transient errors) and back-to-list (invalid candidate id / 404).
 */
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Candidate detail error:', error);
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-error">
          Something went wrong
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold text-brasaland-charcoal">
          Could not load candidate
        </h1>
        <p className="mt-4 text-brasaland-charcoal/70">
          The candidate could not be retrieved. They may have been removed, or the talent pipeline
          service is unavailable.
        </p>
        <div className="mt-6 flex gap-3 justify-center">
          <button
            type="button"
            onClick={reset}
            className="px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-ivory transition-colors"
          >
            Try again
          </button>
          <Link
            href="/"
            className="px-4 py-2 rounded-md border border-brasaland-charcoal/20 text-brasaland-charcoal font-medium hover:bg-brasaland-cream focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-ivory transition-colors"
          >
            Back to list
          </Link>
        </div>
      </div>
    </main>
  );
}
