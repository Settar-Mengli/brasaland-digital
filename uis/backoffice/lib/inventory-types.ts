export type Ingredient = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
  current_stock: number;
};

/** Request body for `POST /inventory/orders/inbound`. */
export type IngredientEntryCreate = {
  ingredient_id: number;
  quantity: number;
  /** Optional purchase cost per unit; omit when unknown. */
  unit_cost?: number;
  supplier_name: string;
  location_id: number;
};

/** Persisted inbound order returned by the inventory API. */
export type IngredientEntryResponse = {
  id: number;
  ingredient_id: number;
  quantity: number;
  /** Purchase cost per unit when recorded; null for historical rows. */
  unit_cost?: number | null;
  supplier_name: string;
  location_id: number;
  created_at: string;
  user_uuid: string;
};

export type IngredientExitCreate = {
  ingredient_id: number;
  quantity: number;
  reason: string;
  location_id: number;
};

export type IngredientExitResponse = {
  id: number;
  ingredient_id: number;
  quantity: number;
  reason: string;
  location_id: number;
  created_at: string;
  user_uuid: string;
};

export type IngredientInfo = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
};

/** Inbound order row nested with ingredient details from `GET /inventory/orders`. */
export type IngredientEntryWithIngredient = {
  id: number;
  ingredient_id: number;
  quantity: number;
  /** Purchase cost per unit when recorded; null for historical rows. */
  unit_cost?: number | null;
  supplier_name: string;
  location_id: number;
  created_at: string;
  user_uuid: string;
  ingredient: IngredientInfo;
};

export type IngredientExitWithIngredient = {
  id: number;
  ingredient_id: number;
  quantity: number;
  reason: string;
  location_id: number;
  created_at: string;
  user_uuid: string;
  ingredient: IngredientInfo;
};

export type OrdersListResponse = {
  entries: IngredientEntryWithIngredient[];
  exits: IngredientExitWithIngredient[];
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
