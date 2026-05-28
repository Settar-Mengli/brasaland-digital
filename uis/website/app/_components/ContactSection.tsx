export default function ContactSection() {
  return (
    <section
      id="contact"
      aria-labelledby="contact-heading"
      className="bg-brasaland-ivory py-20 sm:py-24"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          id="contact-heading"
          className="font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal text-center"
        >
          Get in Touch
        </h2>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          <article className="bg-brasaland-cream rounded-lg p-6 text-center">
            <svg
              className="h-8 w-8 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75"
              />
            </svg>
            <h3 className="mt-3 font-display text-lg font-bold text-brasaland-charcoal">Email</h3>
            <a
              href="mailto:hello@brasaland.com"
              className="mt-2 inline-block text-brasaland-ember hover:underline focus:underline focus:outline-none"
            >
              hello@brasaland.com
            </a>
          </article>
          <article className="bg-brasaland-cream rounded-lg p-6 text-center">
            <svg
              className="h-8 w-8 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z"
              />
            </svg>
            <h3 className="mt-3 font-display text-lg font-bold text-brasaland-charcoal">
              Colombia
            </h3>
            <a
              href="tel:+5741234567"
              className="mt-2 inline-block text-brasaland-ember hover:underline focus:underline focus:outline-none"
            >
              +57 4 123 4567
            </a>
          </article>
          <article className="bg-brasaland-cream rounded-lg p-6 text-center">
            <svg
              className="h-8 w-8 mx-auto text-brasaland-ember"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z"
              />
            </svg>
            <h3 className="mt-3 font-display text-lg font-bold text-brasaland-charcoal">Florida</h3>
            <a
              href="tel:+13051234567"
              className="mt-2 inline-block text-brasaland-ember hover:underline focus:underline focus:outline-none"
            >
              +1 305 123 4567
            </a>
          </article>
        </div>
        <p className="mt-12 text-center text-sm text-brasaland-charcoal/70 max-w-2xl mx-auto">
          Want to place an order? Call your favorite location or visit us directly.{' '}
          <span className="font-semibold text-brasaland-charcoal">
            Online ordering coming soon.
          </span>
        </p>
      </div>
    </section>
  );
}
