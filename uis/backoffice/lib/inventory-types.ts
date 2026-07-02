export type Ingredient = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
  current_stock: number;
};

export type IngredientEntryCreate = {
  ingredient_id: number;
  quantity: number;
  supplier_name: string;
  location_id: number;
};

export type IngredientEntryResponse = {
  id: number;
  ingredient_id: number;
  quantity: number;
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

export type IngredientEntryWithIngredient = {
  id: number;
  ingredient_id: number;
  quantity: number;
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
