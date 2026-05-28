export default function LocationsSection() {
  return (
    <section
      id="locations"
      aria-labelledby="locations-heading"
      className="bg-brasaland-ivory py-20 sm:py-24"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          id="locations-heading"
          className="font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal text-center"
        >
          Our Locations
        </h2>
        <p className="mt-4 text-lg text-brasaland-charcoal/70 text-center max-w-2xl mx-auto">
          14 restaurants across two countries, one consistent experience.
        </p>
        <div className="mt-12 grid gap-8 md:grid-cols-2">
          <article className="bg-brasaland-cream rounded-lg p-8">
            <span aria-hidden="true" className="text-4xl">
              🇨🇴
            </span>
            <h3 className="mt-2 font-display text-2xl font-bold text-brasaland-charcoal">
              Colombia
            </h3>
            <dl>
              <dt className="font-sans text-sm font-semibold uppercase tracking-wide text-brasaland-ember mt-4">
                Restaurants
              </dt>
              <dd className="mt-1 text-brasaland-charcoal/80">
                10 locations across Medellín, Bogotá, and Cali
              </dd>
              <dt className="font-sans text-sm font-semibold uppercase tracking-wide text-brasaland-ember mt-4">
                Hours
              </dt>
              <dd className="mt-1 text-brasaland-charcoal/80">Mon–Sun, 11:00 AM – 10:00 PM</dd>
            </dl>
          </article>
          <article className="bg-brasaland-cream rounded-lg p-8">
            <span aria-hidden="true" className="text-4xl">
              🇺🇸
            </span>
            <h3 className="mt-2 font-display text-2xl font-bold text-brasaland-charcoal">
              United States
            </h3>
            <dl>
              <dt className="font-sans text-sm font-semibold uppercase tracking-wide text-brasaland-ember mt-4">
                Restaurants
              </dt>
              <dd className="mt-1 text-brasaland-charcoal/80">
                4 locations across Miami and Orlando, Florida
              </dd>
              <dt className="font-sans text-sm font-semibold uppercase tracking-wide text-brasaland-ember mt-4">
                Hours
              </dt>
              <dd className="mt-1 text-brasaland-charcoal/80">Mon–Sun, 11:00 AM – 10:00 PM</dd>
            </dl>
          </article>
        </div>
      </div>
    </section>
  );
}
