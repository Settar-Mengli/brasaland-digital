'use client';

import {
  filterActiveLocations,
  filterSalesByLocation,
  sampleLocations,
  sampleSales,
  sortLocationsByCapacity,
} from '@brasaland/operations-toolkit';
import type { Location } from '@brasaland/operations-toolkit';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';

function LocationsContent() {
  const sortedLocations = sortLocationsByCapacity(sampleLocations, 'desc');
  const activeCount = filterActiveLocations(sampleLocations).length;

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Locations</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          All Brasaland restaurant locations — sample dataset (March 2024)
        </p>
      </div>

      {/* Section 1: Summary */}
      <section aria-labelledby="summary-heading" className="mb-10">
        <h2 id="summary-heading" className="font-semibold text-xl mb-4">
          Summary
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total Locations" value={String(sampleLocations.length)} />
          <StatCard label="Active Locations" value={String(activeCount)} />
          <StatCard label="Countries" value="2 (Colombia · USA)" />
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by filterActiveLocations() · @brasaland/operations-toolkit
        </p>
      </section>

      {/* Section 2: Locations table */}
      <section aria-labelledby="locations-heading" className="mb-10">
        <h2 id="locations-heading" className="font-semibold text-xl mb-4">
          All Locations
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse" aria-label="Locations overview">
            <thead className="bg-brasaland-charcoal/5">
              <tr>
                <th scope="col" className="text-left p-3 font-semibold">
                  Name
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  City
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Country
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Status
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Capacity
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Staff
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Manager
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Since
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Rent (USD/mo)
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Sales
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedLocations.map((location) => (
                <LocationRow
                  key={location.id}
                  location={location}
                  salesCount={filterSalesByLocation(sampleSales, location.id).length}
                />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by filterActiveLocations() + sortLocationsByCapacity() + filterSalesByLocation() ·
          @brasaland/operations-toolkit
        </p>
      </section>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4">
        Data shown is the M2 fixture dataset (March 2024). No external API.
      </p>
    </>
  );
}

export default function LocationsPage() {
  return (
    <InventoryAuthGuard>
      <LocationsContent />
    </InventoryAuthGuard>
  );
}

const STATUS_CLASSES: Record<string, string> = {
  Active: 'bg-brasaland-success/10 text-brasaland-success',
  'Temporarily closed': 'bg-brasaland-error/10 text-brasaland-error',
  'Under renovation': 'bg-amber-100 text-amber-800',
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${STATUS_CLASSES[status] ?? ''}`}
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

function LocationRow({ location, salesCount }: { location: Location; salesCount: number }) {
  return (
    <tr className="border-t border-brasaland-charcoal/10">
      <td className="p-3 font-medium">{location.name}</td>
      <td className="p-3">{location.city}</td>
      <td className="p-3">{location.country}</td>
      <td className="p-3">
        <StatusBadge status={location.status} />
      </td>
      <td className="p-3 text-right tabular-nums">{location.seatingCapacity} seats</td>
      <td className="p-3 text-right tabular-nums">{location.staffCount}</td>
      <td className="p-3">{location.manager}</td>
      <td className="p-3 text-right tabular-nums">{location.openingYear}</td>
      <td className="p-3 text-right tabular-nums">
        ${location.monthlyRentCost.USD.toLocaleString()} USD
      </td>
      <td className="p-3 text-right tabular-nums">{salesCount} transactions</td>
    </tr>
  );
}
