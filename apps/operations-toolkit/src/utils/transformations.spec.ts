/** Tests for transformation utilities (financial calculations). */

import { describe, expect, it } from 'vitest';
import {
  calculateDailyRevenue,
  calculateLocationMargin,
  calculateWasteCost,
  convertCurrency,
} from './transformations';
import {
  saleTxn001,
  saleTxn002,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from '../__fixtures__/sample-data';

/** Returns a Date at local midnight matching the given timestamp's local Y/M/D. */
function localDayOf(timestamp: Date): Date {
  return new Date(timestamp.getFullYear(), timestamp.getMonth(), timestamp.getDate());
}

describe('calculateDailyRevenue', () => {
  it('returns the total USD revenue for a specific day', () => {
    const result = calculateDailyRevenue(sampleSales, localDayOf(saleTxn002.timestamp), 'USD');
    expect(result).toBe(5);
  });

  it('returns the total COP revenue for a specific day', () => {
    const result = calculateDailyRevenue(sampleSales, localDayOf(saleTxn002.timestamp), 'COP');
    expect(result).toBe(20000);
  });

  it('includes multiple sales that fall on the same local day', () => {
    const duplicate = { ...saleTxn001, id: 'TXN-X', totalPrice: { USD: 10, COP: 40000 } };
    const result = calculateDailyRevenue(
      [saleTxn001, duplicate],
      localDayOf(saleTxn001.timestamp),
      'USD',
    );
    expect(result).toBe(60);
  });

  it('returns 0 when no sales fall on the target day', () => {
    const farFuture = new Date(2099, 0, 1);
    const result = calculateDailyRevenue(sampleSales, farFuture, 'USD');
    expect(result).toBe(0);
  });

  it('returns 0 when input is empty', () => {
    const result = calculateDailyRevenue([], localDayOf(saleTxn001.timestamp), 'USD');
    expect(result).toBe(0);
  });

  it('rounds the result to 2 decimal places', () => {
    const fractionalSale = { ...saleTxn001, totalPrice: { USD: 1.236, COP: 4944 } };
    const result = calculateDailyRevenue([fractionalSale], localDayOf(saleTxn001.timestamp), 'USD');
    expect(result).toBe(1.24);
  });
});

describe('calculateLocationMargin', () => {
  it('computes margin correctly for a location with multiple sales', () => {
    const result = calculateLocationMargin(sampleSales, sampleMenuItems, 'LOC-MED-01', 'USD');
    expect(result).toBe(60.91);
  });

  it('returns 0 when the location has no sales', () => {
    const result = calculateLocationMargin(sampleSales, sampleMenuItems, 'LOC-UNKNOWN', 'USD');
    expect(result).toBe(0);
  });

  it('returns 0 when sales array is empty', () => {
    const result = calculateLocationMargin([], sampleMenuItems, 'LOC-MED-01', 'USD');
    expect(result).toBe(0);
  });

  it('silently skips sales whose itemId is not in menuItems', () => {
    const unknownSale = { ...saleTxn001, itemId: 'ITEM-UNKNOWN' };
    // only saleTxn001 counts: revenue=50, cost=2×10=20, margin=(30/50)×100=60
    const result = calculateLocationMargin(
      [unknownSale, saleTxn001],
      sampleMenuItems,
      'LOC-MED-01',
      'USD',
    );
    expect(result).toBe(60);
  });

  it('handles COP currency', () => {
    const result = calculateLocationMargin(sampleSales, sampleMenuItems, 'LOC-BOG-01', 'COP');
    expect(result).toBe(64.86);
  });
});

describe('calculateWasteCost', () => {
  it('returns the total USD waste cost for a location', () => {
    const result = calculateWasteCost(sampleWasteRecords, 'LOC-MED-01', 'USD');
    expect(result).toBe(10);
  });

  it('returns the total COP waste cost for a location', () => {
    const result = calculateWasteCost(sampleWasteRecords, 'LOC-BOG-01', 'COP');
    expect(result).toBe(8000);
  });

  it('returns 0 when the location has no waste records', () => {
    const result = calculateWasteCost(sampleWasteRecords, 'LOC-UNKNOWN', 'USD');
    expect(result).toBe(0);
  });

  it('returns 0 when input is empty', () => {
    const result = calculateWasteCost([], 'LOC-MED-01', 'USD');
    expect(result).toBe(0);
  });
});

describe('convertCurrency', () => {
  it('converts USD to COP at the fixed rate', () => {
    expect(convertCurrency(1, 'USD', 'COP')).toBe(4000);
  });

  it('converts COP to USD at the fixed rate', () => {
    expect(convertCurrency(4000, 'COP', 'USD')).toBe(1);
  });

  it('returns the input unchanged when currencies are the same', () => {
    expect(convertCurrency(1234.567, 'USD', 'USD')).toBe(1234.567);
  });

  it('rounds USD→COP results to 2 decimal places', () => {
    expect(convertCurrency(1.234, 'USD', 'COP')).toBe(4936);
  });

  it('rounds COP→USD results to 2 decimal places', () => {
    expect(convertCurrency(5000, 'COP', 'USD')).toBe(1.25);
  });

  it('handles zero amounts', () => {
    expect(convertCurrency(0, 'USD', 'COP')).toBe(0);
    expect(convertCurrency(0, 'COP', 'USD')).toBe(0);
  });
});
