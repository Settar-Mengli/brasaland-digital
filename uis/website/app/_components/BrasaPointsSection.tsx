import Link from 'next/link';
import { formatBrasaPointsEarnLine } from '@brasaland/operations-toolkit';

const CHECK_ICON = (
  <svg
    className="h-6 w-6 flex-none text-brasaland-cream"
    aria-hidden="true"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75 10.5 18.75l9-13.5" />
  </svg>
);

export default function BrasaPointsSection() {
  return (
    <section
      id="brasa-points"
      aria-labelledby="brasa-points-heading"
      className="bg-brasaland-ember py-20 sm:py-24"
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-brasaland-ivory">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-cream">
          Brasa Points
        </p>
        <h2
          id="brasa-points-heading"
          className="mt-3 font-display text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight"
        >
          Earn points with every visit.
        </h2>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 text-left max-w-3xl mx-auto">
          <div className="flex gap-4 items-start">
            {CHECK_ICON}
            <p className="leading-relaxed">{formatBrasaPointsEarnLine()}</p>
          </div>
          <div className="flex gap-4 items-start">
            {CHECK_ICON}
            <p className="leading-relaxed">Redeem your points for discounts and free dishes.</p>
          </div>
          <div className="flex gap-4 items-start">
            {CHECK_ICON}
            <p className="leading-relaxed">Exclusive offers and previews for members.</p>
          </div>
          <div className="flex gap-4 items-start">
            {CHECK_ICON}
            <p className="leading-relaxed">100% digital registration — no more paper cards.</p>
          </div>
        </div>
        <Link
          href="/brasa-points"
          className="mt-12 inline-block bg-brasaland-ivory text-brasaland-ember font-sans font-semibold text-base sm:text-lg px-8 py-3 rounded-md hover:bg-brasaland-cream focus:outline-none focus:ring-2 focus:ring-brasaland-ivory focus:ring-offset-2 focus:ring-offset-brasaland-ember transition-colors"
        >
          Join Brasa Points
        </Link>
      </div>
    </section>
  );
}
