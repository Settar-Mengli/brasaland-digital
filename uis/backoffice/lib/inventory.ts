import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import { handleUnauthorized } from './session';
import { resolveStaffApiBase } from './staff-paths';
import type {
  Ingredient,
  IngredientEntryCreate,
  IngredientEntryResponse,
  IngredientExitCreate,
  IngredientExitResponse,
  OrdersListResponse,
} from './inventory-types';

function getInventoryBaseUrl(): string {
  return resolveStaffApiBase('inventory', 'NEXT_PUBLIC_INVENTORY_API_URL');
}

function requireAccessToken(): string {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  return token;
}

async function inventoryFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getInventoryBaseUrl()}${path}`, init);
  handleUnauthorized(response);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
}

async function inventoryGet<T>(path: string): Promise<T> {
  const token = requireAccessToken();
  return inventoryFetch<T>(path, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

async function inventoryPost<T>(path: string, body: unknown): Promise<T> {
  const token = requireAccessToken();
  return inventoryFetch<T>(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
}

function productsPath(locationId: number): string {
  const params = new URLSearchParams({ location_id: String(locationId) });
  return `/products?${params.toString()}`;
}

export function getProducts(locationId: number): Promise<Ingredient[]> {
  return inventoryGet<Ingredient[]>(productsPath(locationId));
}

export function getProduct(id: number, locationId: number): Promise<Ingredient> {
  const params = new URLSearchParams({ location_id: String(locationId) });
  return inventoryGet<Ingredient>(`/products/${id}?${params.toString()}`);
}

export function createInbound(body: IngredientEntryCreate): Promise<IngredientEntryResponse> {
  return inventoryPost<IngredientEntryResponse>('/orders/inbound', body);
}

export function createOutbound(body: IngredientExitCreate): Promise<IngredientExitResponse> {
  return inventoryPost<IngredientExitResponse>('/orders/outbound', body);
}

export function getOrders(locationId: number): Promise<OrdersListResponse> {
  const params = new URLSearchParams({ location_id: String(locationId) });
  return inventoryGet<OrdersListResponse>(`/orders?${params.toString()}`);
}
