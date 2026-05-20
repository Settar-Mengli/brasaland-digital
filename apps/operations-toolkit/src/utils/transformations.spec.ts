/** Tests for transformation utilities (financial calculations). */

import { describe, expect, it } from 'vitest';
import {
  calculateAverageTicket,
  calculateCountryComparison,
  calculateDailyRevenue,
  calculateLocationMargin,
  calculateWasteCost,
  convertCurrency,
  countSalesByPaymentMethod,
  findTopSellingItems,
  groupWasteByReason,
  rankLocationsByPerformance,
  scoreLocationPerformance,
} from './transformations';
import {
  itemCostilla,
  itemLimonada,
  itemPicanha,
  itemYuca,
  locBogota,
  locCali,
  locMedellin,
  locMiami,
  locNewYork,
  saleTxn001,
  saleTxn002,
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
  wasteRec001,
  wasteRec002,
  wasteRec003,
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

const FIXED_NOW = new Date(2025, 0, 1); // local midnight, deterministic operating-days calculation

describe('scoreLocationPerformance', () => {
  it('computes the composite score for a location with sales', () => {
    const result = scoreLocationPerformance(
      locMedellin,
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result).toBe(6.84);
  });

  it('returns 20 for a location with no sales and no waste', () => {
    const result = scoreLocationPerformance(
      locCali,
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result).toBe(20);
  });

  it('never exceeds 100', () => {
    const result = scoreLocationPerformance(
      locMedellin,
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result).toBeLessThanOrEqual(100);
  });

  it('never goes below 0', () => {
    const result = scoreLocationPerformance(
      locMedellin,
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result).toBeGreaterThanOrEqual(0);
  });
});

describe('rankLocationsByPerformance', () => {
  it('returns locations sorted by score descending', () => {
    const result = rankLocationsByPerformance(
      sampleLocations,
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result.map((r) => r.location.id)).toEqual([
      'LOC-CAL-01',
      'LOC-NYC-01',
      'LOC-BOG-01',
      'LOC-MED-01',
      'LOC-MIA-01',
    ]);
  });

  it('does not mutate the input locations array', () => {
    const input = [...sampleLocations];
    const snapshot = [...sampleLocations];
    rankLocationsByPerformance(input, sampleSales, sampleWasteRecords, sampleMenuItems, FIXED_NOW);
    expect(input).toEqual(snapshot);
  });

  it('returns an empty array when locations is empty', () => {
    const result = rankLocationsByPerformance(
      [],
      sampleSales,
      sampleWasteRecords,
      sampleMenuItems,
      FIXED_NOW,
    );
    expect(result).toEqual([]);
  });
});

describe('countSalesByPaymentMethod', () => {
  it('counts sales by payment method', () => {
    const result = countSalesByPaymentMethod(sampleSales);
    expect(result).toEqual({ Cash: 2, 'Credit card': 2, 'Debit card': 1, 'Digital wallet': 0 });
  });

  it('returns all four keys initialized to 0 for empty input', () => {
    const result = countSalesByPaymentMethod([]);
    expect(result).toEqual({ Cash: 0, 'Credit card': 0, 'Debit card': 0, 'Digital wallet': 0 });
  });

  it('always includes all four payment method keys', () => {
    const result = countSalesByPaymentMethod([saleTxn001]);
    expect(Object.keys(result).sort()).toEqual(
      ['Cash', 'Credit card', 'Debit card', 'Digital wallet'].sort(),
    );
  });
});

describe('calculateAverageTicket', () => {
  it('computes the USD average ticket', () => {
    expect(calculateAverageTicket(sampleSales, 'USD')).toBe(24.4);
  });

  it('computes the COP average ticket', () => {
    expect(calculateAverageTicket(sampleSales, 'COP')).toBe(97600);
  });

  it('returns 0 when input is empty', () => {
    expect(calculateAverageTicket([], 'USD')).toBe(0);
  });
});

describe('findTopSellingItems', () => {
  it('returns the top N items by quantity sold', () => {
    const result = findTopSellingItems(sampleSales, sampleMenuItems, 3);
    expect(result).toEqual([
      { item: itemPicanha, totalSold: 3 },
      { item: itemLimonada, totalSold: 3 },
      { item: itemYuca, totalSold: 1 },
    ]);
  });

  it('returns an empty array when topN <= 0', () => {
    expect(findTopSellingItems(sampleSales, sampleMenuItems, 0)).toEqual([]);
    expect(findTopSellingItems(sampleSales, sampleMenuItems, -1)).toEqual([]);
  });

  it('returns all matched items when topN exceeds the count', () => {
    const result = findTopSellingItems(sampleSales, sampleMenuItems, 100);
    expect(result).toEqual([
      { item: itemPicanha, totalSold: 3 },
      { item: itemLimonada, totalSold: 3 },
      { item: itemYuca, totalSold: 1 },
      { item: itemCostilla, totalSold: 1 },
    ]);
  });

  it('silently skips sales whose itemId is not in menuItems', () => {
    const unknownSale = { ...saleTxn001, itemId: 'ITEM-UNKNOWN' };
    const result = findTopSellingItems([unknownSale, saleTxn001], sampleMenuItems, 5);
    expect(result).toEqual([{ item: itemPicanha, totalSold: 2 }]);
  });

  it('returns an empty array when sales is empty', () => {
    expect(findTopSellingItems([], sampleMenuItems, 3)).toEqual([]);
  });
});

describe('groupWasteByReason', () => {
  it('groups records correctly with all 5 keys present', () => {
    const result = groupWasteByReason(sampleWasteRecords);
    expect(result).toEqual({
      Expired: [wasteRec001],
      'Cooking error': [wasteRec002],
      'Customer return': [wasteRec003],
      Damage: [],
      Other: [],
    });
  });

  it('returns all 5 keys as empty arrays for empty input', () => {
    const result = groupWasteByReason([]);
    expect(result).toEqual({
      Expired: [],
      'Cooking error': [],
      'Customer return': [],
      Damage: [],
      Other: [],
    });
  });

  it('preserves empty arrays for unused reasons', () => {
    const result = groupWasteByReason([wasteRec001]);
    expect(result.Damage).toEqual([]);
    expect(result.Other).toEqual([]);
  });
});

describe('calculateCountryComparison', () => {
  it('computes Colombia metrics correctly', () => {
    const result = calculateCountryComparison(sampleSales, sampleLocations, sampleMenuItems);
    expect(result.Colombia).toEqual({
      totalLocations: 3,
      totalRevenue: { USD: 92, COP: 368000 },
      averageRevenuePerLocation: { USD: 30.67, COP: 122666.67 },
      totalSales: 4,
    });
  });

  it('computes USA metrics correctly', () => {
    const result = calculateCountryComparison(sampleSales, sampleLocations, sampleMenuItems);
    expect(result.USA).toEqual({
      totalLocations: 2,
      totalRevenue: { USD: 30, COP: 120000 },
      averageRevenuePerLocation: { USD: 15, COP: 60000 },
      totalSales: 1,
    });
  });

  it('returns zeros for a country with no locations', () => {
    const result = calculateCountryComparison(sampleSales, [locMiami, locNewYork], sampleMenuItems);
    expect(result.Colombia).toEqual({
      totalLocations: 0,
      totalRevenue: { USD: 0, COP: 0 },
      averageRevenuePerLocation: { USD: 0, COP: 0 },
      totalSales: 0,
    });
  });

  it('returns zero revenue and sales when sales is empty', () => {
    const result = calculateCountryComparison([], sampleLocations, sampleMenuItems);
    expect(result.Colombia.totalRevenue).toEqual({ USD: 0, COP: 0 });
    expect(result.Colombia.totalSales).toBe(0);
    expect(result.USA.totalRevenue).toEqual({ USD: 0, COP: 0 });
    expect(result.USA.totalSales).toBe(0);
  });
});
