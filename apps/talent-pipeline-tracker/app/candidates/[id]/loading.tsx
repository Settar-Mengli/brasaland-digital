/** Route-level loading boundary for the candidate detail page. */
export default function Loading() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-charcoal/60 animate-pulse">
          Loading
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold text-brasaland-charcoal">
          Fetching candidate
        </h1>
      </div>
    </main>
  );
}
