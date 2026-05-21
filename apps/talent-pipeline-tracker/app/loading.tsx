/**
 * Route-level loading boundary for the candidate list page.
 * Shown by Next.js while the Server Component awaits data on first render
 * or on route transitions.
 */
export default function Loading() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-charcoal/60 animate-pulse">
          Loading
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold text-brasaland-charcoal">
          Fetching candidates
        </h1>
      </div>
    </main>
  );
}
