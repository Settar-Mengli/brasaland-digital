import { getAccessToken } from './auth';
import { parseApiError } from './api-error';
import type {
  Ingredient,
  IngredientEntryCreate,
  IngredientEntryResponse,
  IngredientExitCreate,
  IngredientExitResponse,
  OrdersListResponse,
} from './inventory-types';

function getInventoryBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_INVENTORY_API_URL;
  if (!url) {
    throw new Error('NEXT_PUBLIC_INVENTORY_API_URL is not set');
  }
  return url.replace(/\/$/, '');
}

async function inventoryFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getInventoryBaseUrl()}${path}`, init);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
}

async function inventoryPost<T>(path: string, body: unknown): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  return inventoryFetch<T>(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
}

export function getProducts(): Promise<Ingredient[]> {
  return inventoryFetch<Ingredient[]>('/products');
}

export function getProduct(id: number): Promise<Ingredient> {
  return inventoryFetch<Ingredient>(`/products/${id}`);
}

export function createInbound(body: IngredientEntryCreate): Promise<IngredientEntryResponse> {
  return inventoryPost<IngredientEntryResponse>('/orders/inbound', body);
}

export function createOutbound(body: IngredientExitCreate): Promise<IngredientExitResponse> {
  return inventoryPost<IngredientExitResponse>('/orders/outbound', body);
}

export function getOrders(): Promise<OrdersListResponse> {
  return inventoryFetch<OrdersListResponse>('/orders');
}
