export default function FeaturesSection() {
  return (
    <section
      id="features"
      aria-labelledby="features-heading"
      className="bg-brasaland-cream py-20 sm:py-24"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          id="features-heading"
          className="font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal text-center"
        >
          What Makes Us Unique
        </h2>
        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <article className="bg-brasaland-ivory rounded-lg p-8 text-center">
            <svg
              className="h-12 w-12 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z"
              />
            </svg>
            <h3 className="mt-4 font-display text-xl font-bold text-brasaland-charcoal">
              Consistent Quality
            </h3>
            <p className="mt-3 text-brasaland-charcoal/80 leading-relaxed">
              Same recipes and standards in all locations. Fresh ingredients selected daily.
            </p>
          </article>
          <article className="bg-brasaland-ivory rounded-lg p-8 text-center">
            <svg
              className="h-12 w-12 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z"
              />
            </svg>
            <h3 className="mt-4 font-display text-xl font-bold text-brasaland-charcoal">
              Warm Experience
            </h3>
            <p className="mt-3 text-brasaland-charcoal/80 leading-relaxed">
              Friendly, attentive service and a family atmosphere on every visit.
            </p>
          </article>
          <article className="bg-brasaland-ivory rounded-lg p-8 text-center">
            <svg
              className="h-12 w-12 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"
              />
            </svg>
            <h3 className="mt-4 font-display text-xl font-bold text-brasaland-charcoal">Speed</h3>
            <p className="mt-3 text-brasaland-charcoal/80 leading-relaxed">
              Your food ready in minutes — without sacrificing flavor or quality.
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
