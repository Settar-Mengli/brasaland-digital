'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { type FormEvent, useEffect, useState } from 'react';

import InventoryAuthGuard from '@/app/_components/InventoryAuthGuard';
import ProductSelect from '@/app/_components/ProductSelect';
import { createInbound } from '@/lib/inventory';
import { locationSlug, getSessionLocationId } from '@/lib/locations';
import { mapSupplyFailure } from '@/lib/order-failure-codes';
import { track } from '@/lib/telemetry';
import { useOrderFormAbandonment } from '@/lib/use-order-form-abandonment';

const INPUT_CLASS =
  'w-full rounded-md border border-brasaland-charcoal/20 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brasaland-ember';

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

function InboundForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [ingredientId, setIngredientId] = useState<number | ''>(() =>
    parsePreselectedIngredientId(searchParams.get('ingredientId')),
  );
  const [quantity, setQuantity] = useState('');
  const [unitCost, setUnitCost] = useState('');
  const [supplierName, setSupplierName] = useState('');
  const [locationId, setLocationId] = useState(readLocationIdForForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!locationId) {
      router.replace('/login');
    }
  }, [locationId, router]);

  const { onFieldChange } = useOrderFormAbandonment({
    orderType: 'supply',
    locationFormValue: locationId,
    ingredientId,
    submitted,
  });

  function resetForm() {
    setIngredientId('');
    setQuantity('');
    setUnitCost('');
    setSupplierName('');
    const resolvedLocationId = readLocationIdForForm();
    if (!resolvedLocationId) {
      router.replace('/login');
      return;
    }
    setLocationId(resolvedLocationId);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (ingredientId === '') {
      setFormError('Select a product.');
      return;
    }

    const parsedQuantity = Number(quantity);
    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setFormError('quantity must be greater than 0.');
      return;
    }

    const trimmedUnitCost = unitCost.trim();
    let parsedUnitCost: number | undefined;
    if (trimmedUnitCost !== '') {
      parsedUnitCost = Number(trimmedUnitCost);
      if (!Number.isFinite(parsedUnitCost) || parsedUnitCost < 0) {
        setFormError('unit_cost must be a number greater than or equal to 0.');
        return;
      }
    }

    setSubmitting(true);
    try {
      const response = await createInbound({
        ingredient_id: ingredientId,
        quantity: parsedQuantity,
        ...(parsedUnitCost !== undefined ? { unit_cost: parsedUnitCost } : {}),
        supplier_name: supplierName.trim(),
        location_id: Number(locationId),
      });
      const supplyProperties: Record<string, unknown> = {
        supply_order_id: response.id,
        ingredient_id: response.ingredient_id,
        quantity: response.quantity,
        // §8 gap: API uses supplier_name; no supplier directory id yet.
        supplier_id: 0,
        location_id: locationSlug(locationId),
        created_by: response.user_uuid,
      };
      if (typeof response.unit_cost === 'number') {
        supplyProperties.unit_cost = response.unit_cost;
      }
      track('supply_order_created', supplyProperties);
      setSubmitted(true);
      setSuccessMessage('Ingredient entry logged successfully.');
      resetForm();
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : 'Failed to log ingredient entry.';
      track(
        'supply_order_failed',
        mapSupplyFailure(message, ingredientId, Number(quantity), locationSlug(locationId)),
      );
      setFormError(message);
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
          <label htmlFor="inbound-product" className="block text-sm font-medium mb-1">
            Product
          </label>
          <ProductSelect
            id="inbound-product"
            value={ingredientId}
            locationId={Number(locationId)}
            onChange={(value) => {
              onFieldChange();
              setIngredientId(value);
            }}
            disabled={submitting}
          />
        </div>

        <div>
          <label htmlFor="quantity" className="block text-sm font-medium mb-1">
            Quantity
          </label>
          <input
            id="quantity"
            name="quantity"
            type="number"
            min="0.01"
            step="any"
            required
            value={quantity}
            onChange={(event) => {
              onFieldChange();
              setQuantity(event.target.value);
            }}
            className={INPUT_CLASS}
          />
        </div>

        <div>
          <label htmlFor="unit_cost" className="block text-sm font-medium mb-1">
            unit_cost
          </label>
          <input
            id="unit_cost"
            name="unit_cost"
            type="number"
            min={0}
            step="any"
            value={unitCost}
            onChange={(event) => {
              onFieldChange();
              setUnitCost(event.target.value);
            }}
            className={INPUT_CLASS}
          />
          <p className="text-xs text-brasaland-charcoal/40 mt-1">
            Optional purchase cost per unit. Leave blank when unknown.
          </p>
        </div>

        <div>
          <label htmlFor="supplier_name" className="block text-sm font-medium mb-1">
            supplier_name
          </label>
          <input
            id="supplier_name"
            name="supplier_name"
            type="text"
            required
            value={supplierName}
            onChange={(event) => {
              onFieldChange();
              setSupplierName(event.target.value);
            }}
            className={INPUT_CLASS}
          />
        </div>

        <div>
          <label htmlFor="location_id" className="block text-sm font-medium mb-1">
            location_id
          </label>
          <input
            id="location_id"
            name="location_id"
            type="number"
            min={1}
            max={14}
            required
            value={locationId}
            onChange={(event) => {
              onFieldChange();
              setLocationId(event.target.value);
            }}
            className={INPUT_CLASS}
          />
          <p className="text-xs text-brasaland-charcoal/40 mt-1">Receiving location (1–14).</p>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full px-4 py-2 rounded-md bg-brasaland-ember text-white font-medium hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors disabled:opacity-60"
        >
          {submitting ? 'Submitting…' : 'Log inbound order'}
        </button>
      </form>

      <p className="text-xs text-brasaland-charcoal/40 border-t border-brasaland-charcoal/10 pt-4 mt-8">
        POST /inventory/orders/inbound · IngredientEntry
      </p>
    </>
  );
}

export default function InboundOrderPage() {
  return (
    <InventoryAuthGuard>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-brasaland-charcoal">Inbound order</h1>
        <p className="text-sm text-brasaland-charcoal/60 mt-1">
          Log a supplier delivery (IngredientEntry)
        </p>
      </div>
      <InboundForm />
    </InventoryAuthGuard>
  );
}
