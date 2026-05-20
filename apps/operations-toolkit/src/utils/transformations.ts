/** Financial transformation utilities for Brasaland operations data. */

import type { MenuItem, SaleTransaction, WasteRecord } from '../types';

/** Fixed exchange rate used across the operations toolkit: 1 USD = 4000 COP. */
const USD_TO_COP_RATE = 4000;

function roundTo2Decimals(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * Calculates total revenue for all sales on a given calendar day.
 * Returns 0 when the sales array is empty or contains no matching sales.
 * @param sales - All sale transactions to search through.
 * @param date - The target calendar day (year, month, and date are compared).
 * @param currency - The currency to sum totals in.
 * @returns Total revenue rounded to 2 decimal places.
 */
export function calculateDailyRevenue(
  sales: SaleTransaction[],
  date: Date,
  currency: 'USD' | 'COP',
): number {
  const total = sales
    .filter(
      (sale) =>
        sale.timestamp.getFullYear() === date.getFullYear() &&
        sale.timestamp.getMonth() === date.getMonth() &&
        sale.timestamp.getDate() === date.getDate(),
    )
    .reduce((sum, sale) => sum + sale.totalPrice[currency], 0);
  return roundTo2Decimals(total);
}

/**
 * Calculates the gross margin percentage for a location over a set of sales.
 * Sales whose menu item cannot be found in the provided list are skipped.
 * Returns 0 when total revenue is zero to avoid division by zero.
 * @param sales - All sale transactions to consider.
 * @param menuItems - The menu item catalogue used to look up ingredient costs.
 * @param locationId - The location to calculate margin for.
 * @param currency - The currency to use for revenue and cost.
 * @returns Margin as a percentage (0–100), rounded to 2 decimal places.
 */
export function calculateLocationMargin(
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  locationId: string,
  currency: 'USD' | 'COP',
): number {
  const locationSales = sales.filter((sale) => sale.locationId === locationId);
  let revenue = 0;
  let cost = 0;
  for (const sale of locationSales) {
    const menuItem = menuItems.find((item) => item.id === sale.itemId);
    if (menuItem === undefined) continue;
    revenue += sale.totalPrice[currency];
    cost += sale.quantity * menuItem.ingredientCost[currency];
  }
  if (revenue === 0) return 0;
  return roundTo2Decimals(((revenue - cost) / revenue) * 100);
}

/**
 * Calculates the total cost of waste events at a specific location.
 * Returns 0 when the records array is empty or contains no matching records.
 * @param wasteRecords - All waste records to search through.
 * @param locationId - The location to sum waste costs for.
 * @param currency - The currency to sum costs in.
 * @returns Total waste cost rounded to 2 decimal places.
 */
export function calculateWasteCost(
  wasteRecords: WasteRecord[],
  locationId: string,
  currency: 'USD' | 'COP',
): number {
  const total = wasteRecords
    .filter((record) => record.locationId === locationId)
    .reduce((sum, record) => sum + record.cost[currency], 0);
  return roundTo2Decimals(total);
}

/**
 * Converts a monetary amount between USD and COP using the fixed toolkit exchange rate.
 * Returns the amount unchanged (without rounding) when both currencies are the same.
 * @param amount - The monetary amount to convert.
 * @param fromCurrency - The source currency.
 * @param toCurrency - The target currency.
 * @returns The converted amount rounded to 2 decimal places, or the original amount if currencies match.
 */
export function convertCurrency(
  amount: number,
  fromCurrency: 'USD' | 'COP',
  toCurrency: 'USD' | 'COP',
): number {
  if (fromCurrency === toCurrency) return amount;
  if (fromCurrency === 'USD') return roundTo2Decimals(amount * USD_TO_COP_RATE);
  return roundTo2Decimals(amount / USD_TO_COP_RATE);
}
