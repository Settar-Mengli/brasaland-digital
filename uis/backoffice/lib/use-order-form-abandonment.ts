'use client';

import { useCallback, useEffect, useRef } from 'react';

import { locationSlug } from '@/lib/locations';
import { track } from '@/lib/telemetry';

const ABANDON_DEBOUNCE_MS = 30_000;

type OrderFormAbandonmentOptions = {
  orderType: 'supply' | 'consumption';
  locationFormValue: string;
  ingredientId: number | '';
  submitted: boolean;
};

export function useOrderFormAbandonment({
  orderType,
  locationFormValue,
  ingredientId,
  submitted,
}: OrderFormAbandonmentOptions): { onFieldChange: () => void } {
  const formSessionIdRef = useRef(crypto.randomUUID());
  const hasInteractedRef = useRef(false);
  const emittedRef = useRef(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearDebounce = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
  }, []);

  const scheduleAbandon = useCallback(() => {
    clearDebounce();
    debounceTimerRef.current = setTimeout(() => {
      if (emittedRef.current || submitted) {
        return;
      }
      emittedRef.current = true;

      const properties: Record<string, unknown> = {
        order_type: orderType,
        location_id: locationSlug(locationFormValue),
        form_session_id: formSessionIdRef.current,
      };
      if (ingredientId !== '') {
        properties.ingredient_id = ingredientId;
      }
      track('order_form_abandoned', properties);
    }, ABANDON_DEBOUNCE_MS);
  }, [clearDebounce, ingredientId, locationFormValue, orderType, submitted]);

  const onFieldChange = useCallback(() => {
    if (submitted || emittedRef.current) {
      return;
    }
    hasInteractedRef.current = true;
    scheduleAbandon();
  }, [scheduleAbandon, submitted]);

  useEffect(() => {
    if (submitted) {
      clearDebounce();
    }
  }, [clearDebounce, submitted]);

  useEffect(() => clearDebounce, [clearDebounce]);

  return { onFieldChange };
}
