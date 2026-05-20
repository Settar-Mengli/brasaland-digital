/** CountryMetrics type for country-level comparison reports. */

import type { Price } from './price';

/**
 * Aggregated performance metrics for a single country.
 */
export interface CountryMetrics {
  totalLocations: number;
  totalRevenue: Price;
  averageRevenuePerLocation: Price;
  totalSales: number;
}
