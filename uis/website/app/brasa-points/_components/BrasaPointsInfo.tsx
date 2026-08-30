import Link from 'next/link';
import { formatBrasaPointsEarnLine } from '@brasaland/operations-toolkit';

export default function BrasaPointsInfo() {
  const earnLine = formatBrasaPointsEarnLine();

  return (
    <article aria-labelledby="page-heading">
      <section className="mb-10 text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-ember">
          Brasa Points
        </p>
        <h1
          id="page-heading"
          className="mt-3 font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal"
        >
          Learn about Brasa Points
        </h1>
        <p className="mt-6 text-lg text-brasaland-charcoal/80 leading-relaxed">
          Earn points with every visit and redeem them for discounts on your bill at any Brasaland
          location.
        </p>
      </section>

      <section className="space-y-8" aria-labelledby="earn-heading">
        <h2 id="earn-heading" className="font-display text-2xl font-bold text-brasaland-charcoal">
          How you earn
        </h2>
        <p className="text-brasaland-charcoal/80 leading-relaxed">{earnLine}</p>
        <p className="text-brasaland-charcoal/80 leading-relaxed">
          Points do not expire as long as your account stays active with at least one purchase every
          12 months.
        </p>
      </section>

      <section className="mt-10 space-y-4" aria-labelledby="tiers-heading">
        <h2 id="tiers-heading" className="font-display text-2xl font-bold text-brasaland-charcoal">
          Program tiers
        </h2>
        <ul className="space-y-3 text-brasaland-charcoal/80">
          <li>
            <strong>Bronze (0–19 points):</strong> 5% off drinks on Tuesdays.
          </li>
          <li>
            <strong>Silver (20–49 points):</strong> 10% off the main dish, once a month.
          </li>
          <li>
            <strong>Gold (50+ points):</strong> 15% permanent discount and early access to the
            seasonal menu.
          </li>
        </ul>
      </section>

      <section className="mt-10 space-y-4" aria-labelledby="redeem-heading">
        <h2 id="redeem-heading" className="font-display text-2xl font-bold text-brasaland-charcoal">
          Redeeming points
        </h2>
        <p className="text-brasaland-charcoal/80 leading-relaxed">
          Redeem starting at 15 points in increments of 5. Every 5 points equal 20,000 COP or 20 USD
          of discount on the bill. Points cannot be combined with other active monthly promotions.
        </p>
      </section>

      <section className="mt-10 space-y-4" aria-labelledby="cards-heading">
        <h2 id="cards-heading" className="font-display text-2xl font-bold text-brasaland-charcoal">
          Physical cards and the app
        </h2>
        <p className="text-brasaland-charcoal/80 leading-relaxed">
          Brasa Points is available on physical stamp cards (being phased out) and in the digital
          app. You can transfer points from a completed physical card to the app only once by
          presenting the card at any location.
        </p>
      </section>

      <section
        className="mt-10 rounded-lg border border-brasaland-charcoal/10 bg-brasaland-cream p-6"
        aria-labelledby="registration-note-heading"
      >
        <h2
          id="registration-note-heading"
          className="font-display text-xl font-bold text-brasaland-charcoal"
        >
          Registration
        </h2>
        <p className="mt-3 text-brasaland-charcoal/80 leading-relaxed">
          Registration in the mobile app is coming soon. This page does not collect personal
          information.
        </p>
      </section>

      <div className="mt-10">
        <Link
          href="/"
          className="inline-block bg-brasaland-ember text-brasaland-ivory font-sans font-semibold px-8 py-3 rounded-md hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors"
        >
          Back to home
        </Link>
      </div>
    </article>
  );
}
