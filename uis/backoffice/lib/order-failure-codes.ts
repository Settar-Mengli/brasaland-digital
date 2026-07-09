export type SupplyFailureCode = 'ingredient_not_found' | 'validation_error' | 'unknown_supplier';

export type ConsumptionFailureCode = 'insufficient_stock' | 'invalid_reason' | 'validation_error';

export type SupplyFailureProperties = {
  ingredient_id: number;
  quantity: number;
  location_id: string;
  failure_code: SupplyFailureCode;
  failure_message: string;
  supplier_id?: number;
};

export type ConsumptionFailureProperties = {
  ingredient_id: number;
  quantity: number;
  location_id: string;
  failure_code: ConsumptionFailureCode;
  reason?: string;
  available_stock?: number;
};

const INSUFFICIENT_STOCK_PATTERN =
  /Insufficient stock for ingredient .+ Available: ([\d.]+), requested:/;
const INGREDIENT_NOT_FOUND = 'Ingredient not found';
const INVALID_REASON_PREFIX = 'reason must be';

export function mapSupplyFailure(
  message: string,
  ingredientId: number,
  quantity: number,
  locationId: string,
): SupplyFailureProperties {
  let failure_code: SupplyFailureCode = 'validation_error';
  if (message === INGREDIENT_NOT_FOUND) {
    failure_code = 'ingredient_not_found';
  } else if (message.toLowerCase().includes('supplier')) {
    failure_code = 'unknown_supplier';
  }

  return {
    ingredient_id: ingredientId,
    quantity,
    location_id: locationId,
    failure_code,
    failure_message: message,
  };
}

export function mapConsumptionFailure(
  message: string,
  ingredientId: number,
  quantity: number,
  locationId: string,
  reason: string,
): ConsumptionFailureProperties {
  const insufficientMatch = INSUFFICIENT_STOCK_PATTERN.exec(message);
  if (insufficientMatch) {
    const available = Number(insufficientMatch[1]);
    const properties: ConsumptionFailureProperties = {
      ingredient_id: ingredientId,
      quantity,
      location_id: locationId,
      failure_code: 'insufficient_stock',
      reason,
    };
    if (Number.isFinite(available)) {
      properties.available_stock = available;
    }
    return properties;
  }

  if (message.startsWith(INVALID_REASON_PREFIX)) {
    return {
      ingredient_id: ingredientId,
      quantity,
      location_id: locationId,
      failure_code: 'invalid_reason',
      reason,
    };
  }

  if (message === INGREDIENT_NOT_FOUND) {
    return {
      ingredient_id: ingredientId,
      quantity,
      location_id: locationId,
      failure_code: 'validation_error',
      reason,
    };
  }

  return {
    ingredient_id: ingredientId,
    quantity,
    location_id: locationId,
    failure_code: 'validation_error',
    reason,
  };
}
