export default function HomePage() {
  return (
    <section aria-labelledby="welcome-heading">
      <p className="text-sm uppercase tracking-wide text-brasaland-charcoal/60 mb-2">
        Brasaland Operations
      </p>
      <h1 id="welcome-heading" className="font-display text-3xl font-bold mb-3">
        Centralized Incident Manager
      </h1>
      <p className="text-brasaland-charcoal/80 max-w-2xl">
        Register operational incidents, track status across locations, and review chain-wide
        metrics. Registration, list, and summary views will be added in upcoming chunks.
      </p>
    </section>
  );
}
