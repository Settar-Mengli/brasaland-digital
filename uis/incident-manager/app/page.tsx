import Link from 'next/link';

export default function HomePage() {
  return (
    <section aria-labelledby="welcome-heading">
      <p className="text-sm uppercase tracking-wide text-brasaland-charcoal/60 mb-2">
        Brasaland Operations
      </p>
      <h1 id="welcome-heading" className="font-display text-3xl font-bold mb-3">
        Centralized Incident Manager
      </h1>
      <p className="text-brasaland-charcoal/80 max-w-2xl mb-8">
        Register operational incidents, track status across locations, and review chain-wide
        metrics from the live incident API.
      </p>

      <div className="grid gap-4 sm:grid-cols-3 max-w-3xl">
        <Link
          href="/register"
          className="rounded-xl border border-brasaland-charcoal/10 bg-white p-5 shadow-sm hover:border-brasaland-ember/40 transition-colors"
        >
          <h2 className="font-semibold text-lg mb-1">Register</h2>
          <p className="text-sm text-brasaland-charcoal/60">Log a new incident with validation.</p>
        </Link>
        <Link
          href="/incidents"
          className="rounded-xl border border-brasaland-charcoal/10 bg-white p-5 shadow-sm hover:border-brasaland-ember/40 transition-colors"
        >
          <h2 className="font-semibold text-lg mb-1">Incidents</h2>
          <p className="text-sm text-brasaland-charcoal/60">
            Filter the list and update status inline.
          </p>
        </Link>
        <Link
          href="/summary"
          className="rounded-xl border border-brasaland-charcoal/10 bg-white p-5 shadow-sm hover:border-brasaland-ember/40 transition-colors"
        >
          <h2 className="font-semibold text-lg mb-1">Summary</h2>
          <p className="text-sm text-brasaland-charcoal/60">Review totals by status and location.</p>
        </Link>
      </div>
    </section>
  );
}
