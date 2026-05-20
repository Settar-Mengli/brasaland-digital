/** Pure filtering and sorting utilities for Brasaland operations collections. */

import type { Location, MenuCategory, MenuItem, SaleTransaction } from '../types';

/**
 * Returns all sales that occurred at a specific location.
 * @param sales - The full array of sale transactions to filter.
 * @param locationId - The identifier of the location to match.
 * @returns A new array containing only transactions from the given location.
 */
export function filterSalesByLocation(
  sales: SaleTransaction[],
  locationId: string,
): SaleTransaction[] {
  return sales.filter((sale) => sale.locationId === locationId);
}

/**
 * Returns all sales whose timestamp falls within a given date range, inclusive on both ends.
 * @param sales - The full array of sale transactions to filter.
 * @param startDate - The earliest date (inclusive) of the range.
 * @param endDate - The latest date (inclusive) of the range.
 * @returns A new array containing only transactions within the date range.
 */
export function filterSalesByDateRange(
  sales: SaleTransaction[],
  startDate: Date,
  endDate: Date,
): SaleTransaction[] {
  return sales.filter((sale) => {
    const t = sale.timestamp.getTime();
    return t >= startDate.getTime() && t <= endDate.getTime();
  });
}

/**
 * Returns all menu items belonging to a specific category.
 * @param items - The full array of menu items to filter.
 * @param category - The menu category to match.
 * @returns A new array containing only items in the given category.
 */
export function filterMenuItemsByCategory(items: MenuItem[], category: MenuCategory): MenuItem[] {
  return items.filter((item) => item.category === category);
}

/**
 * Returns all locations that are currently active and serving customers.
 * @param locations - The full array of locations to filter.
 * @returns A new array containing only locations with status 'Active'.
 */
export function filterActiveLocations(locations: Location[]): Location[] {
  return locations.filter((loc) => loc.status === 'Active');
}

/**
 * Returns a new array of locations sorted by seating capacity.
 * The original array is never mutated.
 * @param locations - The array of locations to sort.
 * @param order - Sort direction: 'asc' for smallest first, 'desc' for largest first.
 * @returns A new sorted array of locations.
 */
export function sortLocationsByCapacity(locations: Location[], order: 'asc' | 'desc'): Location[] {
  return [...locations].sort((a, b) =>
    order === 'asc' ? a.seatingCapacity - b.seatingCapacity : b.seatingCapacity - a.seatingCapacity,
  );
}

/**
 * Returns a new array of menu items sorted by base price in the specified currency.
 * The original array is never mutated.
 * @param items - The array of menu items to sort.
 * @param currency - The currency to sort by: 'USD' or 'COP'.
 * @param order - Sort direction: 'asc' for lowest price first, 'desc' for highest price first.
 * @returns A new sorted array of menu items.
 */
export function sortMenuItemsByPrice(
  items: MenuItem[],
  currency: 'USD' | 'COP',
  order: 'asc' | 'desc',
): MenuItem[] {
  return [...items].sort((a, b) =>
    order === 'asc'
      ? a.basePrice[currency] - b.basePrice[currency]
      : b.basePrice[currency] - a.basePrice[currency],
  );
}
