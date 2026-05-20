/** Domain types describing individual point-of-sale transactions at Brasaland locations. */

import type { Price } from './price';

/** Payment method used by the customer at the point of sale. */
export type PaymentMethod = 'Cash' | 'Credit card' | 'Debit card' | 'Digital wallet';

/** A single sale event recording one item sold at one location, including payment and staff details. */
export interface SaleTransaction {
  /** Unique identifier, e.g. `"TXN-2024-15482"`. */
  id: string;
  /** Identifier of the location where the sale occurred. */
  locationId: string;
  /** Identifier of the menu item sold. */
  itemId: string;
  /** Number of units sold in this transaction. */
  quantity: number;
  /** Total amount charged, accounting for quantity. */
  totalPrice: Price;
  /** Payment method used by the customer. */
  paymentMethod: PaymentMethod;
  /** Date and time the transaction was recorded. */
  timestamp: Date;
  /** Name of the staff member who handled the transaction. */
  waiterName: string;
}
