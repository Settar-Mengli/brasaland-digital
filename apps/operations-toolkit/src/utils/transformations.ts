/** Financial transformation utilities for Brasaland operations data. */

import type {
  Location,
  MenuItem,
  PaymentMethod,
  SaleTransaction,
  WasteReason,
  WasteRecord,
} from '../types';

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

/**
 * Computes a composite performance score (0–100) for a single location.
 * Score is the sum of four sub-scores: revenue performance (40 pts), operational
 * efficiency (30 pts), waste control (20 pts), and profit margin (10 pts).
 * All currency calculations use USD. The `now` parameter defaults to the current
 * date and is exposed for testability.
 * @param location - The location to score.
 * @param sales - All sale transactions across all locations.
 * @param wasteRecords - All waste records across all locations.
 * @param menuItems - The menu item catalogue for margin calculation.
 * @param now - Reference date for operating-days calculation (defaults to new Date()).
 * @returns A composite score rounded to 2 decimal places.
 */
export function scoreLocationPerformance(
  location: Location,
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
  now?: Date,
): number {
  const effectiveNow = now ?? new Date();

  // Revenue performance (40 pts max)
  const locationSales = sales.filter((sale) => sale.locationId === location.id);
  const totalRevenueUSD = locationSales.reduce((sum, sale) => sum + sale.totalPrice.USD, 0);
  const openingMs = new Date(location.openingYear, 0, 1).getTime();
  const operatingDays = Math.max(1, Math.floor((effectiveNow.getTime() - openingMs) / 86_400_000));
  const avgDailyRevenue = totalRevenueUSD / operatingDays;
  const revenueScore = Math.min(40, (avgDailyRevenue / 1000) * 40);

  // Efficiency (30 pts max)
  const efficiencyScore = Math.min(30, (locationSales.length / location.seatingCapacity) * 30);

  // Waste control (20 pts max)
  const totalWasteCostUSD = calculateWasteCost(wasteRecords, location.id, 'USD');
  const wastePercentage = totalRevenueUSD === 0 ? 0 : (totalWasteCostUSD / totalRevenueUSD) * 100;
  const wasteScore = Math.max(0, 20 - wastePercentage * 2);

  // Profit margin (10 pts max)
  const margin = calculateLocationMargin(sales, menuItems, location.id, 'USD');
  const marginScore = Math.min(10, margin / 10);

  return roundTo2Decimals(revenueScore + efficiencyScore + wasteScore + marginScore);
}

/**
 * Ranks all locations by their composite performance score, highest first.
 * Each entry pairs a location with its computed score. The input array is never mutated.
 * The `now` parameter is forwarded to scoreLocationPerformance for testability.
 * @param locations - The locations to rank.
 * @param sales - All sale transactions across all locations.
 * @param wasteRecords - All waste records across all locations.
 * @param menuItems - The menu item catalogue for margin calculation.
 * @param now - Reference date for operating-days calculation (defaults to new Date()).
 * @returns A new array of location–score pairs sorted by score descending.
 */
export function rankLocationsByPerformance(
  locations: Location[],
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
  now?: Date,
): Array<{ location: Location; score: number }> {
  return [...locations]
    .map((location) => ({
      location,
      score: scoreLocationPerformance(location, sales, wasteRecords, menuItems, now),
    }))
    .sort((a, b) => b.score - a.score);
}

/**
 * Counts the number of sales per payment method.
 * All four payment method keys are always present, initialized to 0.
 * Returns all-zero counts for an empty sales array.
 * @param sales - The sale transactions to count.
 * @returns An object with a count for each PaymentMethod.
 */
export function countSalesByPaymentMethod(sales: SaleTransaction[]): Record<PaymentMethod, number> {
  const result: Record<PaymentMethod, number> = {
    Cash: 0,
    'Credit card': 0,
    'Debit card': 0,
    'Digital wallet': 0,
  };
  for (const sale of sales) {
    result[sale.paymentMethod] += 1;
  }
  return result;
}

/**
 * Calculates the mean transaction total across all sales in the given currency.
 * Returns 0 when the sales array is empty to avoid division by zero.
 * @param sales - The sale transactions to average.
 * @param currency - The currency to use for totals.
 * @returns The average ticket rounded to 2 decimal places.
 */
export function calculateAverageTicket(sales: SaleTransaction[], currency: 'USD' | 'COP'): number {
  if (sales.length === 0) return 0;
  const total = sales.reduce((sum, sale) => sum + sale.totalPrice[currency], 0);
  return roundTo2Decimals(total / sales.length);
}

/**
 * Returns the top N menu items ranked by total quantity sold across all sales.
 * Items whose id does not appear in menuItems are silently skipped.
 * Returns an empty array when topN is 0 or negative, or when no sales exist.
 * If topN exceeds the number of unique matched items, all matched items are returned.
 * @param sales - The sale transactions to aggregate.
 * @param menuItems - The menu item catalogue used to join item details.
 * @param topN - The maximum number of items to return.
 * @returns An array of item–totalSold pairs sorted by totalSold descending.
 */
export function findTopSellingItems(
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  topN: number,
): Array<{ item: MenuItem; totalSold: number }> {
  if (topN <= 0) return [];

  const quantityMap = new Map<string, number>();
  for (const sale of sales) {
    quantityMap.set(sale.itemId, (quantityMap.get(sale.itemId) ?? 0) + sale.quantity);
  }

  const results: Array<{ item: MenuItem; totalSold: number }> = [];
  for (const [itemId, totalSold] of quantityMap) {
    const item = menuItems.find((mi) => mi.id === itemId);
    if (item === undefined) continue;
    results.push({ item, totalSold });
  }

  return results.sort((a, b) => b.totalSold - a.totalSold).slice(0, topN);
}

/**
 * Groups waste records by their reason, returning one array per WasteReason.
 * All five reason keys are always present, initialized to empty arrays.
 * Returns all-empty arrays for an empty input.
 * @param wasteRecords - The waste records to group.
 * @returns An object mapping each WasteReason to its matching records.
 */
export function groupWasteByReason(
  wasteRecords: WasteRecord[],
): Record<WasteReason, WasteRecord[]> {
  const result: Record<WasteReason, WasteRecord[]> = {
    Expired: [],
    'Cooking error': [],
    'Customer return': [],
    Damage: [],
    Other: [],
  };
  for (const record of wasteRecords) {
    result[record.reason].push(record);
  }
  return result;
}
