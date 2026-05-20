/** Domain types describing items available on the Brasaland menu. */

import type { Price } from './price';

/** Top-level grouping for every item sold at a Brasaland location. */
export type MenuCategory = 'Meat' | 'Side' | 'Beverage' | 'Dessert' | 'Combo';

/** Lifecycle state of a menu item — controls availability for ordering and reporting. */
export type MenuItemStatus = 'Active' | 'Seasonal' | 'Discontinued';

/** A single item offered on the Brasaland menu, including pricing and availability per market. */
export interface MenuItem {
  /** Unique identifier, e.g. `"ITEM-PICANHA-250"`. */
  id: string;
  /** Display name of the item. */
  name: string;
  /** Top-level menu category this item belongs to. */
  category: MenuCategory;
  /** Customer-facing sale price in both operating currencies. */
  basePrice: Price;
  /** Internal cost of ingredients used to prepare one unit. */
  ingredientCost: Price;
  /** Estimated time in minutes to prepare one unit. */
  prepTimeMinutes: number;
  /** Whether this item is offered at Colombian locations. */
  isAvailableInColombia: boolean;
  /** Whether this item is offered at U.S. locations. */
  isAvailableInUSA: boolean;
  /** List of allergen identifiers associated with this item. */
  allergens: string[];
  /** Current lifecycle state of this menu item. */
  status: MenuItemStatus;
}
