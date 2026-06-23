'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Website global error:', error);
  }, [error]);

  return (
    <html lang="en">
      <body className="font-sans bg-brasaland-ivory text-brasaland-charcoal antialiased min-h-screen flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <p className="text-sm font-semibold tracking-widest uppercase text-brasaland-error">
            Something went wrong
          </p>
          <h1 className="mt-3 text-3xl font-bold">Brasaland</h1>
          <p className="mt-4 text-brasaland-charcoal/70">
            A critical error occurred. Please try again or return to the home page.
          </p>
          <div className="mt-6 flex gap-3 justify-center">
            <button
              type="button"
              onClick={reset}
              className="px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium"
            >
              Try again
            </button>
            <a
              href="/"
              className="px-4 py-2 rounded-md border border-brasaland-charcoal/20 text-brasaland-charcoal font-medium"
            >
              Home
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
