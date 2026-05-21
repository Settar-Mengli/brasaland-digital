'use client';

import { useEffect } from 'react';

/**
 * Route-level error boundary for the candidate list page.
 * Catches errors thrown during Server Component render (e.g. ApiError from
 * listCandidates) and renders a recoverable UI with a "Try again" button.
 */
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface for local debugging; in production this should route to a
    // proper observability sink, but this keeps the dev loop visible.
    console.error('Candidate list error:', error);
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-error">
          Something went wrong
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold text-brasaland-charcoal">
          Could not load candidates
        </h1>
        <p className="mt-4 text-brasaland-charcoal/70">
          The talent pipeline service did not respond as expected. Please try again — if the problem
          persists, check the API configuration.
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-6 inline-flex items-center px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-ivory transition-colors"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
