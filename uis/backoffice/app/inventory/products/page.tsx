'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import { getProducts } from '@/lib/inventory';
import type { Ingredient } from '@/lib/inventory-types';
import { getSessionLocationId, getSessionLocationSlug } from '@/lib/locations';
import { getStockLevel, type StockLevel } from '@/lib/stock-level';
import { track } from '@/lib/telemetry';

const STOCK_BADGE_CLASSES: Record<StockLevel, string> = {
  healthy: 'bg-brasaland-success/10 text-brasaland-success',
  low: 'bg-amber-100 text-amber-800',
  empty: 'bg-brasaland-error/10 text-brasaland-error',
};

function StockIndicator({ currentStock }: { currentStock: number }) {
  const { level, label } = getStockLevel(currentStock);
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${STOCK_BADGE_CLASSES[level]}`}
    >
      {label}
    </span>
  );
}

function ProductsContent() {
  const [products, setProducts] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      try {
        const locationId = getSessionLocationId();
        const data = await getProducts(locationId);
        if (!cancelled) {
          setProducts(data);
          const locationSlug = getSessionLocationSlug();
          if (locationSlug) {
            track('ingredient_list_viewed', {
              location_id: locationSlug,
              item_count: data.length,
            });
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          const message =
            loadError instanceof Error ? loadError.message : 'Failed to load ingredients.';
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProducts();

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className="text-sm text-brasaland-charcoal/60">Loading ingredients…</p>;
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
      <section aria-labelledby="products-heading" className="mb-10">
        <h2 id="products-heading" className="font-semibold text-xl mb-4">
          All Ingredients
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse" aria-label="Ingredient inventory">
            <thead className="bg-brasaland-charcoal/5">
              <tr>
                <th scope="col" className="text-left p-3 font-semibold">
                  Name
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  SKU
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Unit
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Category
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Country
                </th>
                <th scope="col" className="text-right p-3 font-semibold">
                  current_stock
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Stock
                </th>
                <th scope="col" className="text-left p-3 font-semibold">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {products.map((ingredient) => (
                <tr key={ingredient.id} className="border-t border-brasaland-charcoal/10">
                  <td className="p-3 font-medium">{ingredient.name}</td>
                  <td className="p-3">{ingredient.sku}</td>
                  <td className="p-3">{ingredient.unit}</td>
                  <td className="p-3">{ingredient.category}</td>
                  <td className="p-3">{ingredient.country}</td>
                  <td className="p-3 text-right tabular-nums">{ingredient.current_stock}</td>
                  <td className="p-3">
                    <StockIndicator currentStock={ingredient.current_stock} />
                  </td>
                  <td className="p-3">
                    <div className="flex flex-col gap-1 text-sm">
                      <Link
                        href={`/inventory/orders/inbound?ingredientId=${ingredient.id}`}
                        className="text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded-sm"
                      >
                        Inbound order
                      </Link>
                      <Link
                        href={`/inventory/orders/outbound?ingredientId=${ingredient.id}`}
                        className="text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded-sm"
                      >
                        Outbound order
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-brasaland-charcoal/40 mt-2">
          Powered by getProducts() · GET /inventory/products?location_id=
        </p>
      </section>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4">
        Live ingredient data from the Brasaland Inventory API. current_stock is computed per
        location from entries minus exits.
      </p>
    </>
  );
}

export default function ProductsPage() {
  return (
    <InventoryAuthGuard>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Inventory</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Ingredients with computed current_stock · Brasaland Inventory API
        </p>
      </div>
      <ProductsContent />
    </InventoryAuthGuard>
  );
}
