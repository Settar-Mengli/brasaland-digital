/** Tests for entity validators. */

import { describe, expect, it } from 'vitest';
import { validateLocation, validateMenuItem, validateSaleTransaction } from './validations';
import { itemPicanha, locMedellin, saleTxn001 } from '../__fixtures__/sample-data';

const FIXED_NOW = new Date(2025, 5, 15); // June 15, 2025

describe('validateMenuItem', () => {
  it('returns valid for a fully valid item', () => {
    expect(validateMenuItem(itemPicanha)).toEqual({ valid: true, errors: [] });
  });

  it('fails when basePrice.USD is 0', () => {
    const result = validateMenuItem({ ...itemPicanha, basePrice: { USD: 0, COP: 100000 } });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('basePrice.USD must be greater than 0');
  });

  it('fails when basePrice.COP is 0', () => {
    const result = validateMenuItem({ ...itemPicanha, basePrice: { USD: 25, COP: 0 } });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('basePrice.COP must be greater than 0');
  });

  it('fails when prepTimeMinutes is 0', () => {
    const result = validateMenuItem({ ...itemPicanha, prepTimeMinutes: 0 });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('prepTimeMinutes must be greater than 0');
  });

  it('fails when prepTimeMinutes exceeds 60', () => {
    const result = validateMenuItem({ ...itemPicanha, prepTimeMinutes: 61 });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('prepTimeMinutes must be 60 or less');
  });

  it('fails when name is whitespace-only', () => {
    const result = validateMenuItem({ ...itemPicanha, name: '   ' });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('name must not be empty');
  });

  it('fails when item is unavailable in both countries', () => {
    const result = validateMenuItem({
      ...itemPicanha,
      isAvailableInColombia: false,
      isAvailableInUSA: false,
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('item must be available in at least one country');
  });

  it('collects multiple errors at once', () => {
    const result = validateMenuItem({
      ...itemPicanha,
      basePrice: { USD: 0, COP: 100000 },
      name: '   ',
    });
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBe(2);
    expect(result.errors).toContain('basePrice.USD must be greater than 0');
    expect(result.errors).toContain('name must not be empty');
  });
});

describe('validateSaleTransaction', () => {
  it('returns valid for a fully valid sale', () => {
    expect(validateSaleTransaction(saleTxn001)).toEqual({ valid: true, errors: [] });
  });

  it('fails when quantity is 0', () => {
    const result = validateSaleTransaction({ ...saleTxn001, quantity: 0 });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('quantity must be greater than 0');
  });

  it('fails when totalPrice.USD is 0', () => {
    const result = validateSaleTransaction({
      ...saleTxn001,
      totalPrice: { USD: 0, COP: 200000 },
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('totalPrice.USD must be greater than 0');
  });

  it('fails when totalPrice.COP is 0', () => {
    const result = validateSaleTransaction({
      ...saleTxn001,
      totalPrice: { USD: 50, COP: 0 },
    });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('totalPrice.COP must be greater than 0');
  });

  it('fails when waiterName is whitespace-only', () => {
    const result = validateSaleTransaction({ ...saleTxn001, waiterName: '   ' });
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('waiterName must not be empty');
  });

  it('collects multiple errors at once', () => {
    const result = validateSaleTransaction({
      ...saleTxn001,
      quantity: 0,
      waiterName: '   ',
    });
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBe(2);
    expect(result.errors).toContain('quantity must be greater than 0');
    expect(result.errors).toContain('waiterName must not be empty');
  });
});

describe('validateLocation', () => {
  it('returns valid for a fully valid location', () => {
    expect(validateLocation(locMedellin, FIXED_NOW)).toEqual({ valid: true, errors: [] });
  });

  it('fails when openingYear is before 2008', () => {
    const result = validateLocation({ ...locMedellin, openingYear: 2000 }, FIXED_NOW);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('openingYear must be 2008 or later');
  });

  it('fails when openingYear is in the future', () => {
    const result = validateLocation({ ...locMedellin, openingYear: 2030 }, FIXED_NOW);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('openingYear must not be in the future');
  });

  it('fails when seatingCapacity is 0', () => {
    const result = validateLocation({ ...locMedellin, seatingCapacity: 0 }, FIXED_NOW);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('seatingCapacity must be greater than 0');
  });

  it('fails when staffCount is 0', () => {
    const result = validateLocation({ ...locMedellin, staffCount: 0 }, FIXED_NOW);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('staffCount must be greater than 0');
  });

  it('fails when monthlyRentCost.USD is 0', () => {
    const result = validateLocation(
      { ...locMedellin, monthlyRentCost: { USD: 0, COP: 8000000 } },
      FIXED_NOW,
    );
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('monthlyRentCost.USD must be greater than 0');
  });

  it('fails when monthlyRentCost.COP is 0', () => {
    const result = validateLocation(
      { ...locMedellin, monthlyRentCost: { USD: 2000, COP: 0 } },
      FIXED_NOW,
    );
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('monthlyRentCost.COP must be greater than 0');
  });

  it('fails when averageMonthlyUtilities.USD is 0', () => {
    const result = validateLocation(
      { ...locMedellin, averageMonthlyUtilities: { USD: 0, COP: 2000000 } },
      FIXED_NOW,
    );
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('averageMonthlyUtilities.USD must be greater than 0');
  });

  it('fails when averageMonthlyUtilities.COP is 0', () => {
    const result = validateLocation(
      { ...locMedellin, averageMonthlyUtilities: { USD: 500, COP: 0 } },
      FIXED_NOW,
    );
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('averageMonthlyUtilities.COP must be greater than 0');
  });

  it('collects multiple errors at once', () => {
    const result = validateLocation(
      { ...locMedellin, seatingCapacity: 0, staffCount: 0 },
      FIXED_NOW,
    );
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBe(2);
    expect(result.errors).toContain('seatingCapacity must be greater than 0');
    expect(result.errors).toContain('staffCount must be greater than 0');
  });

  it('defaults to current date when now is omitted', () => {
    const futureYear = new Date().getFullYear() + 5;
    const result = validateLocation({ ...locMedellin, openingYear: futureYear });
    expect(result.errors).toContain('openingYear must not be in the future');
  });
});
