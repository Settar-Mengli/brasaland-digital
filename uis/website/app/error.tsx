'use client';

import Link from 'next/link';
import { useEffect } from 'react';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Website error:', error);
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-error">
          Something went wrong
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold text-brasaland-charcoal">
          This page could not be loaded
        </h1>
        <p className="mt-4 text-brasaland-charcoal/70">
          An unexpected error occurred. Please try again or return to the home page.
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
            Home
          </Link>
        </div>
      </div>
    </main>
  );
}
