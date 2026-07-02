import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const INVENTORY_BASE = 'http://localhost:3003/api/inventory';

describe('inventory client', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_INVENTORY_API_URL', INVENTORY_BASE);
    vi.stubGlobal('window', globalThis);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'test-access-token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    });
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('getProducts calls the products URL without auth', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([{ id: 1, name: 'Beef brisket', current_stock: 60 }]), {
        status: 200,
      }),
    );

    const { getProducts } = await import('./inventory');
    await getProducts();

    expect(fetchMock).toHaveBeenCalledWith(`${INVENTORY_BASE}/products`, undefined);
  });

  it('createInbound sends Bearer token on POST', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 1, ingredient_id: 1, quantity: 10 }), { status: 200 }),
    );

    const { createInbound } = await import('./inventory');
    await createInbound({
      ingredient_id: 1,
      quantity: 10,
      supplier_name: 'Carnes del Valle S.A.',
      location_id: 1,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${INVENTORY_BASE}/orders/inbound`,
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token',
          'Content-Type': 'application/json',
        }),
      }),
    );
  });

  it('propagates API error messages from parseApiError', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail:
            "Insufficient stock for ingredient 'Beef brisket'. Available: 60.0, requested: 100.0.",
        }),
        { status: 400, statusText: 'Bad Request' },
      ),
    );

    const { createOutbound } = await import('./inventory');
    await expect(
      createOutbound({
        ingredient_id: 1,
        quantity: 100,
        reason: 'consumption',
        location_id: 1,
      }),
    ).rejects.toThrow(
      "Insufficient stock for ingredient 'Beef brisket'. Available: 60.0, requested: 100.0.",
    );
  });
});
