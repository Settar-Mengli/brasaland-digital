/** Tests for search utilities. */

import { describe, expect, it } from 'vitest';
import { binarySearchLocationByCapacity, findLocationById, findMenuItemByName } from './search';
import {
  itemPicanha,
  locBogota,
  locCali,
  locMedellin,
  locMiami,
  locNewYork,
  sampleLocations,
  sampleMenuItems,
} from '../__fixtures__/sample-data';

describe('findLocationById', () => {
  it('returns the location whose id matches', () => {
    const result = findLocationById(sampleLocations, 'LOC-MED-01');
    expect(result).toEqual(locMedellin);
  });

  it('returns null when no location matches', () => {
    const result = findLocationById(sampleLocations, 'LOC-UNKNOWN');
    expect(result).toBe(null);
  });

  it('returns null when input is empty', () => {
    const result = findLocationById([], 'LOC-MED-01');
    expect(result).toBe(null);
  });
});

describe('findMenuItemByName', () => {
  it('returns the item whose name matches exactly', () => {
    const result = findMenuItemByName(sampleMenuItems, 'Picanha 250g');
    expect(result).toEqual(itemPicanha);
  });

  it('matches case-insensitively with a lowercase search term', () => {
    const result = findMenuItemByName(sampleMenuItems, 'picanha 250g');
    expect(result).toEqual(itemPicanha);
  });

  it('matches when the search term is uppercase', () => {
    const result = findMenuItemByName(sampleMenuItems, 'PICANHA 250G');
    expect(result).toEqual(itemPicanha);
  });

  it('returns null when no item matches', () => {
    const result = findMenuItemByName(sampleMenuItems, 'Nonexistent Item');
    expect(result).toBe(null);
  });

  it('returns null when input is empty', () => {
    const result = findMenuItemByName([], 'Picanha 250g');
    expect(result).toBe(null);
  });
});

describe('binarySearchLocationByCapacity', () => {
  const sortedByCapacity = [locCali, locMiami, locMedellin, locNewYork, locBogota];
  // Capacities: 50, 60, 80, 100, 120

  it('finds an element in the middle of the array', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 80)).toBe(2);
  });

  it('finds the element at the start of the array', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 50)).toBe(0);
  });

  it('finds the element at the end of the array', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 120)).toBe(4);
  });

  it('returns -1 when the target capacity is not present', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 90)).toBe(-1);
  });

  it('returns -1 when the target is below the minimum', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 10)).toBe(-1);
  });

  it('returns -1 when the target is above the maximum', () => {
    expect(binarySearchLocationByCapacity(sortedByCapacity, 200)).toBe(-1);
  });

  it('returns -1 when input is empty', () => {
    expect(binarySearchLocationByCapacity([], 80)).toBe(-1);
  });

  it('finds the only element in a single-element array', () => {
    expect(binarySearchLocationByCapacity([locMedellin], 80)).toBe(0);
  });

  it('returns -1 when a single-element array does not contain the target', () => {
    expect(binarySearchLocationByCapacity([locMedellin], 999)).toBe(-1);
  });
});
