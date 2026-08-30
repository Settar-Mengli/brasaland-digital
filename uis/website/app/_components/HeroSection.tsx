import Link from 'next/link';

export default function HeroSection() {
  return (
    <section
      id="hero"
      aria-labelledby="hero-heading"
      className="bg-brasaland-cream py-20 sm:py-28 lg:py-36"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <h1
          id="hero-heading"
          className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-brasaland-charcoal leading-tight"
        >
          The taste of the grill, in every bite.
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-brasaland-charcoal/80 leading-relaxed">
          Since 2008, serving the best grilled meats in Colombia and the United States. 14
          locations, one passion for quality and flavor.
        </p>
        <Link
          href="/brasa-points"
          className="mt-10 inline-block bg-brasaland-ember text-brasaland-ivory font-sans font-semibold text-base sm:text-lg px-8 py-3 rounded-md hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 focus:ring-offset-brasaland-cream transition-colors"
        >
          Learn about Brasa Points
        </Link>
      </div>
    </section>
  );
}
