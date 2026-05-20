/** Domain types describing food or inventory waste events recorded at Brasaland locations. */

import type { Price } from './price';

/** Reason a waste event was recorded — used for loss analysis and operational reporting. */
export type WasteReason = 'Expired' | 'Cooking error' | 'Customer return' | 'Damage' | 'Other';

/** A single waste event, capturing what was lost, why, and at what cost. */
export interface WasteRecord {
  /** Unique identifier for this waste record. */
  id: string;
  /** Identifier of the location where the waste occurred. */
  locationId: string;
  /** Identifier of the menu item that was wasted. */
  itemId: string;
  /** Number of units wasted in this event. */
  quantity: number;
  /** Reason the waste was incurred. */
  reason: WasteReason;
  /** Total cost of the wasted inventory at ingredient cost. */
  cost: Price;
  /** Date and time the waste event was recorded. */
  timestamp: Date;
  /** Name of the staff member who logged this record. */
  reportedBy: string;
}
