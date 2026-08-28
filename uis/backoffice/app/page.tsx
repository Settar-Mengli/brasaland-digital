'use client';

import Link from 'next/link';
import type { CountryMetrics } from '@brasaland/operations-toolkit';
import {
  calculateAverageTicket,
  calculateCountryComparison,
  countSalesByPaymentMethod,
  filterActiveLocations,
  findTopSellingItems,
  rankLocationsByPerformance,
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from '@brasaland/operations-toolkit';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';

function DashboardContent() {
  const countryMetrics = calculateCountryComparison(sampleSales, sampleLocations, sampleMenuItems);
  const rankedLocations = rankLocationsByPerformance(
    sampleLocations,
    sampleSales,
    sampleWasteRecords,
    sampleMenuItems,
  );
  const topSellers = findTopSellingItems(sampleSales, sampleMenuItems, 4);
  const paymentBreakdown = countSalesByPaymentMethod(sampleSales);
  const avgTicketUSD = calculateAverageTicket(sampleSales, 'USD');
  const activeLocations = filterActiveLocations(sampleLocations);

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">
          Operations Dashboard
        </h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Sample data · March 2024 · {sampleSales.length} transactions · {sampleLocations.length}{' '}
          locations
        </p>
      </div>

      {/* Section 1: Country Comparison */}
      <section aria-labelledby="country-heading" className="mb-10">
        <h2 id="country-heading" className="font-semibold text-xl mb-4">
          Country Comparison
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CountryCard label="Colombia" metrics={countryMetrics.Colombia} />
          <CountryCard label="USA" metrics={countryMetrics.USA} />
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by calculateCountryComparison() · @brasaland/operations-toolkit
        </p>
      </section>

      {/* Section 2: Location Rankings */}
      <section aria-labelledby="rankings-heading" className="mb-10">
        <h2 id="rankings-heading" className="font-semibold text-xl mb-4">
          Location Performance Rankings
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse" aria-labelledby="rankings-heading">
            <thead className="bg-brasaland-charcoal/5">
              <tr>
                <th scope="col" className="text-left p-3 font-semibold">
                  Rank
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Location
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Country
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Status
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Score
                </th>
              </tr>
            </thead>
            <tbody>
              {rankedLocations.map(({ location, score }, i) => (
                <tr key={location.id} className="border-t border-brasaland-charcoal/10">
                  <td className="p-3">{i + 1}</td>
                  <td className="p-3 font-medium">{location.name}</td>
                  <td className="p-3">{location.country}</td>
                  <td className="p-3">
                    <StatusBadge status={location.status} />
                  </td>
                  <td className="p-3 text-right tabular-nums">{score.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by rankLocationsByPerformance() · @brasaland/operations-toolkit
        </p>
        <div className="mt-4">
          <Link
            href="/locations"
            className="text-sm font-medium text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded-sm"
          >
            View all locations →
          </Link>
        </div>
      </section>

      {/* Section 3: Top Sellers + Payment Methods */}
      <section aria-labelledby="sellers-heading" className="mb-10">
        <h2 id="sellers-heading" className="font-semibold text-xl mb-4">
          Sales Breakdown
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-3">Top Sellers</h3>
            <ol className="space-y-2">
              {topSellers.map(({ item, totalSold }, i) => (
                <li key={item.id} className="flex justify-between text-sm">
                  <span>
                    {i + 1}. {item.name}
                  </span>
                  <span className="font-medium tabular-nums">{totalSold} sold</span>
                </li>
              ))}
            </ol>
            <p className="text-xs text-brasaland-charcoal/40 mt-3">
              Powered by findTopSellingItems()
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-3">Payment Methods</h3>
            <dl className="space-y-2">
              {(Object.entries(paymentBreakdown) as Array<[string, number]>).map(
                ([method, count]) => (
                  <div key={method} className="flex justify-between text-sm">
                    <dt>{method}</dt>
                    <dd className="font-medium tabular-nums">{count}</dd>
                  </div>
                ),
              )}
            </dl>
            <p className="text-xs text-brasaland-charcoal/40 mt-3">
              Powered by countSalesByPaymentMethod()
            </p>
          </div>
        </div>
      </section>

      {/* Section 4: Summary Stats */}
      <section aria-labelledby="summary-heading" className="mb-10">
        <h2 id="summary-heading" className="font-semibold text-xl mb-4">
          Summary
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Average Ticket" value={`$${avgTicketUSD.toFixed(2)} USD`} />
          <StatCard
            label="Active Locations"
            value={`${activeLocations.length} / ${sampleLocations.length}`}
          />
          <StatCard
            label="Dataset"
            value={`${sampleSales.length} sales · ${sampleLocations.length} locations`}
          />
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by calculateAverageTicket() + filterActiveLocations() ·
          @brasaland/operations-toolkit
        </p>
      </section>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4">
        Data shown is the M2 fixture dataset (March 2024). No external API.
      </p>
    </>
  );
}

export default function DashboardPage() {
  return (
    <InventoryAuthGuard>
      <DashboardContent />
    </InventoryAuthGuard>
  );
}

function CountryCard({ label, metrics }: { label: string; metrics: CountryMetrics }) {
  return (
    <div className="border border-brasaland-charcoal/10 rounded-lg p-4 bg-white">
      <h3 className="font-display font-semibold text-lg mb-3">{label}</h3>
      <dl className="space-y-1 text-sm">
        <div>
          <dt className="inline text-brasaland-charcoal/60">Locations: </dt>
          <dd className="inline font-medium">{metrics.totalLocations}</dd>
        </div>
        <div>
          <dt className="inline text-brasaland-charcoal/60">Revenue: </dt>
          <dd className="inline font-medium">${metrics.totalRevenue.USD} USD</dd>
        </div>
        <div>
          <dt className="inline text-brasaland-charcoal/60">Avg per location: </dt>
          <dd className="inline font-medium">${metrics.averageRevenuePerLocation.USD} USD</dd>
        </div>
        <div>
          <dt className="inline text-brasaland-charcoal/60">Total sales: </dt>
          <dd className="inline font-medium">{metrics.totalSales}</dd>
        </div>
      </dl>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const classes: Record<string, string> = {
    Active: 'bg-brasaland-success/10 text-brasaland-success',
    'Temporarily closed': 'bg-brasaland-error/10 text-brasaland-error',
    'Under renovation': 'bg-yellow-100 text-yellow-800',
  };
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${classes[status] ?? ''}`}
    >
      {status}
    </span>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-brasaland-charcoal/10 rounded-lg p-4 bg-white">
      <dt className="text-xs text-brasaland-charcoal/60 uppercase tracking-wide">{label}</dt>
      <dd className="mt-1 text-xl font-semibold">{value}</dd>
    </div>
  );
}
