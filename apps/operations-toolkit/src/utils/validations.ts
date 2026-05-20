/** Entity validators for Brasaland operations data. */

import type { Location, MenuItem, SaleTransaction, ValidationResult } from '../types';

/**
 * Validates a menu item against its business rules.
 * All rules are checked — errors are not short-circuited.
 * @param item - The menu item to validate.
 * @returns A ValidationResult with valid=true when all rules pass.
 */
export function validateMenuItem(item: MenuItem): ValidationResult {
  const errors: string[] = [];
  if (item.basePrice.USD <= 0) errors.push('basePrice.USD must be greater than 0');
  if (item.basePrice.COP <= 0) errors.push('basePrice.COP must be greater than 0');
  if (item.prepTimeMinutes <= 0) errors.push('prepTimeMinutes must be greater than 0');
  if (item.prepTimeMinutes > 60) errors.push('prepTimeMinutes must be 60 or less');
  if (item.name.trim() === '') errors.push('name must not be empty');
  if (!item.isAvailableInColombia && !item.isAvailableInUSA)
    errors.push('item must be available in at least one country');
  return { valid: errors.length === 0, errors };
}

/**
 * Validates a sale transaction against its business rules.
 * All rules are checked — errors are not short-circuited.
 * @param sale - The sale transaction to validate.
 * @returns A ValidationResult with valid=true when all rules pass.
 */
export function validateSaleTransaction(sale: SaleTransaction): ValidationResult {
  const errors: string[] = [];
  if (sale.quantity <= 0) errors.push('quantity must be greater than 0');
  if (sale.totalPrice.USD <= 0) errors.push('totalPrice.USD must be greater than 0');
  if (sale.totalPrice.COP <= 0) errors.push('totalPrice.COP must be greater than 0');
  if (sale.waiterName.trim() === '') errors.push('waiterName must not be empty');
  return { valid: errors.length === 0, errors };
}

/**
 * Validates a location against its business rules.
 * All rules are checked — errors are not short-circuited.
 * The now parameter defaults to the current date and is exposed for deterministic testing.
 * @param location - The location to validate.
 * @param now - Reference date for the current-year check (defaults to new Date()).
 * @returns A ValidationResult with valid=true when all rules pass.
 */
export function validateLocation(location: Location, now?: Date): ValidationResult {
  const errors: string[] = [];
  const currentYear = (now ?? new Date()).getFullYear();
  if (location.openingYear < 2008) errors.push('openingYear must be 2008 or later');
  if (location.openingYear > currentYear) errors.push('openingYear must not be in the future');
  if (location.seatingCapacity <= 0) errors.push('seatingCapacity must be greater than 0');
  if (location.staffCount <= 0) errors.push('staffCount must be greater than 0');
  if (location.monthlyRentCost.USD <= 0) errors.push('monthlyRentCost.USD must be greater than 0');
  if (location.monthlyRentCost.COP <= 0) errors.push('monthlyRentCost.COP must be greater than 0');
  if (location.averageMonthlyUtilities.USD <= 0)
    errors.push('averageMonthlyUtilities.USD must be greater than 0');
  if (location.averageMonthlyUtilities.COP <= 0)
    errors.push('averageMonthlyUtilities.COP must be greater than 0');
  return { valid: errors.length === 0, errors };
}
