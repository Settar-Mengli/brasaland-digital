'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { type FormEvent, useEffect, useState } from 'react';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import ProductSelect from '@/app/_components/ProductSelect';
import { createOutbound, getProduct } from '@/lib/inventory';
import { locationSlug, getSessionLocationId } from '@/lib/locations';
import { mapConsumptionFailure } from '@/lib/order-failure-codes';
import { track } from '@/lib/telemetry';
import { useOrderFormAbandonment } from '@/lib/use-order-form-abandonment';

const INPUT_CLASS =
  'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';

const REASON_OPTIONS = [
  { value: 'consumption', label: 'consumption' },
  { value: 'waste', label: 'waste' },
] as const;

function parsePreselectedIngredientId(value: string | null): number | '' {
  if (!value) {
    return '';
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : '';
}

function readLocationIdForForm(): string {
  if (typeof window === 'undefined') {
    return '';
  }
  try {
    return String(getSessionLocationId());
  } catch {
    return '';
  }
}

function OutboundForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [ingredientId, setIngredientId] = useState<number | ''>(() =>
    parsePreselectedIngredientId(searchParams.get('ingredientId')),
  );
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState<'consumption' | 'waste'>('consumption');
  const [locationId, setLocationId] = useState(readLocationIdForForm);
  const [currentStock, setCurrentStock] = useState<number | null>(null);
  const [stockLoading, setStockLoading] = useState(ingredientId !== '');
  const [stockError, setStockError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [quantityError, setQuantityError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const { onFieldChange } = useOrderFormAbandonment({
    orderType: 'consumption',
    locationFormValue: locationId,
    ingredientId,
    submitted,
  });

  useEffect(() => {
    if (!locationId) {
      router.replace('/login');
    }
  }, [locationId, router]);

  useEffect(() => {
    if (ingredientId === '') {
      return;
    }

    const selectedId = ingredientId;
    const selectedLocationId = Number(locationId);
    let cancelled = false;

    async function loadStock() {
      setStockLoading(true);
      setStockError(null);
      try {
        const product = await getProduct(selectedId, selectedLocationId);
        if (!cancelled) {
          setCurrentStock(product.current_stock);
        }
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : 'Failed to load current stock.';
          setCurrentStock(null);
          setStockError(message);
        }
      } finally {
        if (!cancelled) {
          setStockLoading(false);
        }
      }
    }

    void loadStock();

    return () => {
      cancelled = true;
    };
  }, [ingredientId, locationId]);

  const parsedQuantity = quantity === '' ? null : Number(quantity);
  const showClientWarning =
    currentStock !== null &&
    parsedQuantity !== null &&
    Number.isFinite(parsedQuantity) &&
    parsedQuantity > currentStock;

  function resetForm() {
    setIngredientId('');
    setQuantity('');
    setReason('consumption');
    const resolvedLocationId = readLocationIdForForm();
    if (!resolvedLocationId) {
      router.replace('/login');
      return;
    }
    setLocationId(resolvedLocationId);
    setCurrentStock(null);
    setStockLoading(false);
    setStockError(null);
    setQuantityError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setQuantityError(null);
    setSuccessMessage(null);

    if (ingredientId === '') {
      setFormError('Select a product.');
      return;
    }

    const parsedQuantity = Number(quantity);
    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setQuantityError('quantity must be greater than 0.');
      return;
    }

    setSubmitting(true);
    try {
      const response = await createOutbound({
        ingredient_id: ingredientId,
        quantity: parsedQuantity,
        reason,
        location_id: Number(locationId),
      });
      track('consumption_order_created', {
        consumption_order_id: response.id,
        ingredient_id: response.ingredient_id,
        quantity: response.quantity,
        reason: response.reason as 'consumption' | 'waste',
        location_id: locationSlug(locationId),
        created_by: response.user_uuid,
        restricted_access: false,
      });
      setSubmitted(true);
      setSuccessMessage('Ingredient exit logged successfully.');
      resetForm();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : 'Failed to log ingredient exit.';
      track(
        'consumption_order_failed',
        mapConsumptionFailure(
          message,
          ingredientId,
          Number(quantity),
          locationSlug(locationId),
          reason,
        ),
      );
      if (message.startsWith('Insufficient stock for ingredient')) {
        setQuantityError(message);
      } else {
        setFormError(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="mb-6">
        <Link
          href="/inventory/products"
          className="text-sm font-medium text-brasaland-ember hover:underline focus:outline-none focus:ring-2 focus:ring-brasaland-ember rounded-sm"
        >
          ← Back to inventory
        </Link>
      </div>

      <form
        onSubmit={handleSubmit}
        className="max-w-lg border border-brasaland-charcoal/10 rounded-lg p-6 bg-white space-y-4"
      >
        {successMessage ? (
          <p
            role="status"
            className="text-sm text-brasaland-success bg-brasaland-success/10 rounded-md px-3 py-2"
          >
            {successMessage}
          </p>
        ) : null}

        {formError ? (
          <p
            role="alert"
            className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2"
          >
            {formError}
          </p>
        ) : null}

        <div>
          <label htmlFor="outbound-product" className="block text-sm font-medium mb-1">
            Product
          </label>
          <ProductSelect
            id="outbound-product"
            value={ingredientId}
            locationId={Number(locationId)}
            onChange={(value) => {
              onFieldChange();
              setIngredientId(value);
              setCurrentStock(null);
              setStockError(null);
              setStockLoading(true);
            }}
            disabled={submitting}
          />
        </div>

        {ingredientId !== '' ? (
          <div className="rounded-md border border-brasaland-charcoal/10 bg-brasaland-cream/30 px-3 py-2">
            <p className="text-sm text-brasaland-charcoal/70">
              current_stock:{' '}
              {stockLoading ? (
                <span>Loading…</span>
              ) : stockError ? (
                <span className="text-brasaland-error">{stockError}</span>
              ) : (
                <span className="font-semibold text-brasaland-charcoal tabular-nums">
                  {currentStock ?? '—'}
                </span>
              )}
            </p>
          </div>
        ) : null}

        <div>
          <label htmlFor="outbound-quantity" className="block text-sm font-medium mb-1">
            Quantity
          </label>
          <input
            id="outbound-quantity"
            name="quantity"
            type="number"
            min="0.01"
            step="any"
            required
            value={quantity}
            onChange={(event) => {
              onFieldChange();
              setQuantity(event.target.value);
              setQuantityError(null);
            }}
            className={INPUT_CLASS}
            aria-invalid={quantityError !== null}
            aria-describedby={quantityError ? 'outbound-quantity-error' : undefined}
          />
          {showClientWarning ? (
            <p
              role="status"
              className="text-sm text-amber-800 bg-amber-100 rounded-md px-3 py-2 mt-2"
            >
              Warning: requested quantity ({parsedQuantity}) exceeds available stock ({currentStock}
              ).
            </p>
          ) : null}
          {quantityError ? (
            <p
              id="outbound-quantity-error"
              role="alert"
              className="text-sm text-brasaland-error bg-brasaland-error/10 rounded-md px-3 py-2 mt-2"
            >
              {quantityError}
            </p>
          ) : null}
        </div>

        <div>
          <label htmlFor="reason" className="block text-sm font-medium mb-1">
            reason
          </label>
          <select
            id="reason"
            name="reason"
            required
            value={reason}
            onChange={(event) => {
              onFieldChange();
              setReason(event.target.value as 'consumption' | 'waste');
            }}
            className={INPUT_CLASS}
          >
            {REASON_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="outbound-location_id" className="block text-sm font-medium mb-1">
            location_id
          </label>
          <input
            id="outbound-location_id"
            name="location_id"
            type="number"
            min={1}
            max={14}
            required
            value={locationId}
            onChange={(event) => {
              onFieldChange();
              setLocationId(event.target.value);
              setCurrentStock(null);
              setStockError(null);
              setStockLoading(ingredientId !== '');
            }}
            className={INPUT_CLASS}
          />
          <p className="text-xs text-brasaland-charcoal/40 mt-1">
            Location where the exit occurred (1–14).
          </p>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
        >
          {submitting ? 'Submitting…' : 'Log outbound order'}
        </button>
      </form>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4 mt-8">
        POST /inventory/orders/outbound · IngredientExit
      </p>
    </>
  );
}

export default function OutboundOrderPage() {
  return (
    <InventoryAuthGuard>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Outbound order</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Log consumption or waste (IngredientExit)
        </p>
      </div>
      <OutboundForm />
    </InventoryAuthGuard>
  );
}
