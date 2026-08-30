'use client';

import { useEffect, useState } from 'react';
import AdminAuthGuard from '../_components/AdminAuthGuard';
import { getWeeklyLocationPerformance } from '../../lib/reporting';
import type {
  LocationPerformanceItem,
  WeeklyLocationPerformanceResponse,
} from '../../lib/reporting-types';

type ViewState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: WeeklyLocationPerformanceResponse };

const moneyFormatterByCurrency: Record<string, Intl.NumberFormat> = {
  COP: new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }),
  USD: new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }),
};

const ratioFormatter = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const weekLabelFormatter = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' });

function formatMoney(amount: number, currency: string): string {
  const formatter = moneyFormatterByCurrency[currency];
  if (formatter) {
    return formatter.format(amount);
  }
  return `${amount.toLocaleString('en-US')} ${currency}`;
}

function formatWeekPeriod(weekStart: string | null): string {
  if (!weekStart) {
    return 'No week computed yet';
  }
  const start = new Date(`${weekStart}T00:00:00Z`);
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + 6);
  return `${weekLabelFormatter.format(start)} – ${weekLabelFormatter.format(end)} (UTC)`;
}

function locationLabel(slug: string): string {
  return slug
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function ReportingContent() {
  const [view, setView] = useState<ViewState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const data = await getWeeklyLocationPerformance();
        if (!cancelled) {
          setView({ status: 'success', data });
        }
      } catch (error) {
        if (!cancelled) {
          setView({
            status: 'error',
            message: error instanceof Error ? error.message : 'Failed to load report.',
          });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">
          Weekly Location Cost &amp; Waste Report
        </h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Purchase cost, waste, stockouts, and price alerts by location
        </p>
      </div>

      {view.status === 'loading' ? (
        <p role="status" className="text-sm text-brasaland-charcoal/60">
          Loading weekly performance…
        </p>
      ) : null}

      {view.status === 'error' ? (
        <p
          role="alert"
          className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
        >
          {view.message}
        </p>
      ) : null}

      {view.status === 'success' ? (
        <section aria-labelledby="reporting-heading">
          <h2 id="reporting-heading" className="font-semibold text-xl mb-2">
            Week period
          </h2>
          <p className="text-sm text-brasaland-charcoal/70 mb-6">
            {formatWeekPeriod(view.data.week_start)}
            {view.data.week_start ? (
              <span className="text-brasaland-charcoal/40">
                {' '}
                · week_start {view.data.week_start}
              </span>
            ) : null}
          </p>

          {view.data.locations.length === 0 ? (
            <p className="text-sm text-brasaland-charcoal/60">
              No location rows for this week. Run the reporting pipeline, then refresh.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table
                className="w-full text-sm border-collapse"
                aria-label="Weekly location cost and waste"
              >
                <thead className="bg-brasaland-charcoal/5">
                  <tr>
                    <th scope="col" className="text-left p-3 font-semibold">
                      Location
                    </th>
                    <th scope="col" className="text-left p-3 font-semibold">
                      Country
                    </th>
                    <th scope="col" className="text-right p-3 font-semibold">
                      Purchase Cost per Location
                    </th>
                    <th scope="col" className="text-right p-3 font-semibold">
                      Waste Cost per Location
                    </th>
                    <th scope="col" className="text-right p-3 font-semibold">
                      Waste Ratio
                    </th>
                    <th scope="col" className="text-right p-3 font-semibold">
                      Stockout Frequency
                    </th>
                    <th scope="col" className="text-right p-3 font-semibold">
                      Price Alert Frequency
                    </th>
                    <th scope="col" className="text-left p-3 font-semibold">
                      Currency
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {view.data.locations.map((row: LocationPerformanceItem) => (
                    <tr key={row.location_id} className="border-t border-brasaland-charcoal/10">
                      <td className="p-3">{locationLabel(row.location_id)}</td>
                      <td className="p-3">{row.country}</td>
                      <td className="p-3 text-right">
                        {formatMoney(row.total_purchase_cost, row.currency)}
                      </td>
                      <td className="p-3 text-right">
                        {formatMoney(row.total_waste_cost, row.currency)}
                      </td>
                      <td className="p-3 text-right">{ratioFormatter.format(row.waste_ratio)}</td>
                      <td className="p-3 text-right">{row.stockout_events_count}</td>
                      <td className="p-3 text-right">{row.price_alert_events_count}</td>
                      <td className="p-3">{row.currency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}
    </>
  );
}

export default function ReportingPage() {
  return (
    <AdminAuthGuard>
      <ReportingContent />
    </AdminAuthGuard>
  );
}
