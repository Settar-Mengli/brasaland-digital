/** Pure search utilities for Brasaland operations collections. */

import type { Location, MenuItem } from '../types';

/**
 * Finds a location by its unique identifier using linear search.
 * @param locations - The array of locations to search.
 * @param id - The location identifier to match.
 * @returns The matching location, or null if not found.
 */
export function findLocationById(locations: Location[], id: string): Location | null {
  return locations.find((loc) => loc.id === id) ?? null;
}

/**
 * Finds a menu item by name using a case-insensitive linear search.
 * @param items - The array of menu items to search.
 * @param name - The item name to match (case-insensitive).
 * @returns The first matching menu item, or null if not found.
 */
export function findMenuItemByName(items: MenuItem[], name: string): MenuItem | null {
  const lowerName = name.toLowerCase();
  return items.find((item) => item.name.toLowerCase() === lowerName) ?? null;
}

/**
 * Finds the index of a location with a given seating capacity using iterative binary search.
 * Assumes the input array is sorted ascending by seatingCapacity.
 * @param sortedLocations - Locations sorted ascending by seatingCapacity.
 * @param targetCapacity - The seating capacity to find.
 * @returns The index of the matching location, or -1 if not found.
 */
export function binarySearchLocationByCapacity(
  sortedLocations: Location[],
  targetCapacity: number,
): number {
  let low = 0;
  let high = sortedLocations.length - 1;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const location = sortedLocations[mid]; // Location | undefined under noUncheckedIndexedAccess
    if (location === undefined) return -1;
    if (location.seatingCapacity === targetCapacity) return mid;
    if (location.seatingCapacity < targetCapacity) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return -1;
}
