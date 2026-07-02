'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { getOrders } from '@/lib/inventory';
import type {
  IngredientEntryWithIngredient,
  IngredientExitWithIngredient,
} from '@/lib/inventory-types';

type OrderType = 'Inbound' | 'Outbound';

type OrderRow = {
  key: string;
  productName: string;
  quantity: number;
  unit: string;
  type: OrderType;
  createdAt: string;
  userUuid: string;
  sortTime: number;
};

const TYPE_BADGE_CLASSES: Record<OrderType, string> = {
  Inbound: 'bg-brasaland-success/10 text-brasaland-success',
  Outbound: 'bg-brasaland-ember/10 text-brasaland-ember',
};

function toInboundRow(entry: IngredientEntryWithIngredient): OrderRow {
  return {
    key: `entry-${entry.id}`,
    productName: entry.ingredient.name,
    quantity: entry.quantity,
    unit: entry.ingredient.unit,
    type: 'Inbound',
    createdAt: entry.created_at,
    userUuid: entry.user_uuid,
    sortTime: new Date(entry.created_at).getTime(),
  };
}

function toOutboundRow(exitRecord: IngredientExitWithIngredient): OrderRow {
  return {
    key: `exit-${exitRecord.id}`,
    productName: exitRecord.ingredient.name,
    quantity: exitRecord.quantity,
    unit: exitRecord.ingredient.unit,
    type: 'Outbound',
    createdAt: exitRecord.created_at,
    userUuid: exitRecord.user_uuid,
    sortTime: new Date(exitRecord.created_at).getTime(),
  };
}

function formatCreatedAt(isoDate: string): string {
  const parsed = new Date(isoDate);
  if (Number.isNaN(parsed.getTime())) {
    return isoDate;
  }
  return parsed.toLocaleString();
}

function OrdersContent() {
  const [rows, setRows] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadOrders() {
      try {
        const data = await getOrders();
        if (!cancelled) {
          const merged = [...data.entries.map(toInboundRow), ...data.exits.map(toOutboundRow)].sort(
            (left, right) => right.sortTime - left.sortTime,
          );
          setRows(merged);
        }
      } catch (loadError) {
        if (!cancelled) {
          const message = loadError instanceof Error ? loadError.message : 'Failed to load orders.';
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadOrders();

    return () => {
      cancelled = true;
    };
  }, []);

  const orderCountLabel = useMemo(() => {
    const inbound = rows.filter((row) => row.type === 'Inbound').length;
    const outbound = rows.filter((row) => row.type === 'Outbound').length;
    return `${rows.length} orders · ${inbound} inbound · ${outbound} outbound`;
  }, [rows]);

  if (loading) {
    return <p className="text-sm text-brasaland-charcoal/60">Loading orders…</p>;
  }

  if (error) {
    return (
      <p
        role="alert"
        className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
      >
        {error}
      </p>
    );
  }

  return (
    <>
      <section aria-labelledby="orders-heading" className="mb-10">
        <h2 id="orders-heading" className="font-semibold text-xl mb-4">
          Order history
        </h2>
        <p className="text-sm text-brasaland-charcoal/60 mb-4">{orderCountLabel}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse" aria-label="Ingredient order history">
            <thead className="bg-brasaland-charcoal/5">
              <tr>
                <th scope="col" className="text-left p-3 font-semibold">
                  Product
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  Quantity
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Type
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Created
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  user_uuid
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-3 text-brasaland-charcoal/60">
                    No orders recorded yet.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.key} className="border-t border-brasaland-charcoal/10">
                    <td className="p-3 font-medium">{row.productName}</td>
                    <td className="p-3 text-right tabular-nums">
                      {row.quantity} {row.unit}
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${TYPE_BADGE_CLASSES[row.type]}`}
                      >
                        {row.type}
                      </span>
                    </td>
                    <td className="p-3">{formatCreatedAt(row.createdAt)}</td>
                    <td className="p-3">{row.userUuid}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by getOrders() · GET /inventory/orders
        </p>
      </section>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4">
        Read-only view of IngredientEntry and IngredientExit records. No edit or delete actions.
      </p>
    </>
  );
}

export default function OrdersPage() {
  return (
    <InventoryAuthGuard>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Orders</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Inbound deliveries and outbound consumption or waste
        </p>
      </div>
      <div className="mb-6">
        <Link
          href="/inventory/products"
          className="text-sm font-medium text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded-sm"
        >
          ← Back to inventory
        </Link>
      </div>
      <OrdersContent />
    </InventoryAuthGuard>
  );
}
