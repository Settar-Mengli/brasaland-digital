/** Tests for collection utilities. */

import { describe, expect, it } from 'vitest';
import {
  filterActiveLocations,
  filterMenuItemsByCategory,
  filterSalesByDateRange,
  filterSalesByLocation,
  sortLocationsByCapacity,
  sortMenuItemsByPrice,
} from './collections';
import {
  itemCostilla,
  itemPicanha,
  locBogota,
  locCali,
  locMedellin,
  locMiami,
  locNewYork,
  saleTxn001,
  saleTxn002,
  saleTxn003,
  saleTxn004,
  sampleLocations,
  sampleMenuItems,
  sampleSales,
} from '../__fixtures__/sample-data';

describe('filterSalesByLocation', () => {
  it('returns only sales matching the given location id', () => {
    const result = filterSalesByLocation(sampleSales, 'LOC-MED-01');
    expect(result).toEqual([saleTxn001, saleTxn002]);
  });

  it('returns an empty array when no sales match', () => {
    const result = filterSalesByLocation(sampleSales, 'LOC-UNKNOWN');
    expect(result).toEqual([]);
  });

  it('returns an empty array when input is empty', () => {
    const result = filterSalesByLocation([], 'LOC-MED-01');
    expect(result).toEqual([]);
  });

  it('does not mutate the input array', () => {
    const input = [...sampleSales];
    const snapshot = [...sampleSales];
    filterSalesByLocation(input, 'LOC-MED-01');
    expect(input).toEqual(snapshot);
  });
});

describe('filterSalesByDateRange', () => {
  it('returns sales within the inclusive range', () => {
    const result = filterSalesByDateRange(
      sampleSales,
      new Date('2024-03-10T00:00:00Z'),
      new Date('2024-03-20T19:00:00Z'),
    );
    expect(result).toEqual([saleTxn002, saleTxn003, saleTxn004]);
  });

  it('includes sales whose timestamp equals startDate', () => {
    const result = filterSalesByDateRange(
      sampleSales,
      new Date('2024-03-10T14:30:00Z'),
      new Date('2024-03-10T14:30:00Z'),
    );
    expect(result).toEqual([saleTxn002]);
  });

  it('includes sales whose timestamp equals endDate', () => {
    const result = filterSalesByDateRange(
      sampleSales,
      new Date('2024-03-20T19:00:00Z'),
      new Date('2024-03-20T19:00:00Z'),
    );
    expect(result).toEqual([saleTxn004]);
  });

  it('excludes sales before startDate and after endDate', () => {
    const result = filterSalesByDateRange(
      sampleSales,
      new Date('2024-03-10T00:00:00Z'),
      new Date('2024-03-20T19:00:00Z'),
    );
    expect(result.map((s) => s.id)).not.toContain('TXN-001');
    expect(result.map((s) => s.id)).not.toContain('TXN-005');
  });

  it('returns an empty array when startDate is after endDate', () => {
    const result = filterSalesByDateRange(
      sampleSales,
      new Date('2024-03-31T00:00:00Z'),
      new Date('2024-03-01T00:00:00Z'),
    );
    expect(result).toEqual([]);
  });

  it('returns an empty array when input is empty', () => {
    const result = filterSalesByDateRange(
      [],
      new Date('2024-03-01T00:00:00Z'),
      new Date('2024-03-31T00:00:00Z'),
    );
    expect(result).toEqual([]);
  });
});

describe('filterMenuItemsByCategory', () => {
  it('returns only items in the given category', () => {
    const result = filterMenuItemsByCategory(sampleMenuItems, 'Meat');
    expect(result).toEqual([itemPicanha, itemCostilla]);
  });

  it('returns an empty array when no items match', () => {
    const result = filterMenuItemsByCategory(sampleMenuItems, 'Dessert');
    expect(result).toEqual([]);
  });

  it('returns an empty array when input is empty', () => {
    const result = filterMenuItemsByCategory([], 'Meat');
    expect(result).toEqual([]);
  });
});

describe('filterActiveLocations', () => {
  it('returns only locations with status Active', () => {
    const result = filterActiveLocations(sampleLocations);
    expect(result).toEqual([locMedellin, locBogota, locMiami]);
  });

  it('excludes locations with non-Active statuses', () => {
    const result = filterActiveLocations(sampleLocations);
    expect(result).not.toContainEqual(locCali);
    expect(result).not.toContainEqual(locNewYork);
  });

  it('returns an empty array when no locations are Active', () => {
    const result = filterActiveLocations([locCali, locNewYork]);
    expect(result).toEqual([]);
  });

  it('returns an empty array when input is empty', () => {
    const result = filterActiveLocations([]);
    expect(result).toEqual([]);
  });
});

describe('sortLocationsByCapacity', () => {
  it('sorts ascending by seatingCapacity', () => {
    const result = sortLocationsByCapacity(sampleLocations, 'asc');
    expect(result.map((loc) => loc.seatingCapacity)).toEqual([50, 60, 80, 100, 120]);
  });

  it('sorts descending by seatingCapacity', () => {
    const result = sortLocationsByCapacity(sampleLocations, 'desc');
    expect(result.map((loc) => loc.seatingCapacity)).toEqual([120, 100, 80, 60, 50]);
  });

  it('does not mutate the input array', () => {
    const input = [...sampleLocations];
    const snapshot = [...sampleLocations];
    sortLocationsByCapacity(input, 'asc');
    expect(input).toEqual(snapshot);
  });

  it('returns an empty array when input is empty', () => {
    const result = sortLocationsByCapacity([], 'asc');
    expect(result).toEqual([]);
  });
});

describe('sortMenuItemsByPrice', () => {
  it('sorts ascending by USD price', () => {
    const result = sortMenuItemsByPrice(sampleMenuItems, 'USD', 'asc');
    expect(result.map((item) => item.basePrice.USD)).toEqual([4, 5, 25, 30]);
  });

  it('sorts descending by USD price', () => {
    const result = sortMenuItemsByPrice(sampleMenuItems, 'USD', 'desc');
    expect(result.map((item) => item.basePrice.USD)).toEqual([30, 25, 5, 4]);
  });

  it('sorts ascending by COP price', () => {
    const result = sortMenuItemsByPrice(sampleMenuItems, 'COP', 'asc');
    expect(result.map((item) => item.basePrice.COP)).toEqual([16000, 20000, 100000, 120000]);
  });

  it('sorts descending by COP price', () => {
    const result = sortMenuItemsByPrice(sampleMenuItems, 'COP', 'desc');
    expect(result.map((item) => item.basePrice.COP)).toEqual([120000, 100000, 20000, 16000]);
  });

  it('does not mutate the input array', () => {
    const input = [...sampleMenuItems];
    const snapshot = [...sampleMenuItems];
    sortMenuItemsByPrice(input, 'USD', 'asc');
    expect(input).toEqual(snapshot);
  });

  it('returns an empty array when input is empty', () => {
    const result = sortMenuItemsByPrice([], 'USD', 'asc');
    expect(result).toEqual([]);
  });
});
