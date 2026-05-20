/** Domain types describing Brasaland's physical restaurant locations. */

import type { Price } from './price';

/** Country in which a Brasaland location operates. */
export type Country = 'Colombia' | 'USA';

/** Operational state of a location — determines whether it is currently serving customers. */
export type LocationStatus = 'Active' | 'Temporarily closed' | 'Under renovation';

/** A single Brasaland restaurant location, including operational metadata and fixed cost structure. */
export interface Location {
  /** Unique identifier, e.g. `"LOC-MEDELLIN-01"`. */
  id: string;
  /** Display name of the location. */
  name: string;
  /** City where the location is situated. */
  city: string;
  /** Country in which this location operates. */
  country: Country;
  /** Calendar year the location first opened. */
  openingYear: number;
  /** Total number of guest seats available. */
  seatingCapacity: number;
  /** Current number of staff employed at this location. */
  staffCount: number;
  /** Monthly rental cost for the premises. */
  monthlyRentCost: Price;
  /** Average monthly spend on utilities (electricity, water, gas). */
  averageMonthlyUtilities: Price;
  /** Full name of the location's general manager. */
  manager: string;
  /** Current operational status of the location. */
  status: LocationStatus;
}
