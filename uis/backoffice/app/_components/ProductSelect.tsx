'use client';

import { useEffect, useState } from 'react';

import { getProducts } from '@/lib/inventory';
import type { Ingredient } from '@/lib/inventory-types';

const SELECT_CLASS =
  'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';

type ProductSelectProps = {
  id?: string;
  value: number | '';
  onChange: (ingredientId: number) => void;
  disabled?: boolean;
};

export default function ProductSelect({
  id = 'product',
  value,
  onChange,
  disabled = false,
}: ProductSelectProps) {
  const [products, setProducts] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      try {
        const data = await getProducts();
        if (!cancelled) {
          setProducts(data);
        }
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : 'Failed to load ingredients.';
          setLoadError(message);
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

  if (loadError) {
    return (
      <p role="alert" className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2">
        {loadError}
      </p>
    );
  }

  return (
    <select
      id={id}
      value={value}
      disabled={disabled || loading}
      required
      onChange={(event) => onChange(Number(event.target.value))}
      className={SELECT_CLASS}
    >
      <option value="" disabled>
        {loading ? 'Loading products…' : 'Select a product…'}
      </option>
      {products.map((product) => (
        <option key={product.id} value={product.id}>
          {product.name}
        </option>
      ))}
    </select>
  );
}
