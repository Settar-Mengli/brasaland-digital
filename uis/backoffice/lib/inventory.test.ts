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

  it('getProducts calls the products URL with location_id and Bearer auth', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([{ id: 1, name: 'Beef brisket', current_stock: 60 }]), {
        status: 200,
      }),
    );

    const { getProducts } = await import('./inventory');
    await getProducts(1);

    expect(fetchMock).toHaveBeenCalledWith(
      `${INVENTORY_BASE}/products?location_id=1`,
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token',
        }),
      }),
    );
  });

  it('getOrders scopes the request to location_id with Bearer auth', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ entries: [], exits: [] }), { status: 200 }),
    );

    const { getOrders } = await import('./inventory');
    await getOrders(11);

    expect(fetchMock).toHaveBeenCalledWith(
      `${INVENTORY_BASE}/orders?location_id=11`,
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-access-token',
        }),
      }),
    );
  });

  it('clears the session and redirects on 401', async () => {
    const assignMock = vi.fn();
    vi.stubGlobal('window', {
      ...globalThis,
      localStorage,
      location: { assign: assignMock },
    });

    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(null, { status: 401, statusText: 'Unauthorized' }),
    );

    const { getProducts } = await import('./inventory');
    await expect(getProducts(1)).rejects.toThrow('Unauthorized');
    expect(localStorage.removeItem).toHaveBeenCalledWith('brasaland_access_token');
    expect(assignMock).toHaveBeenCalledWith('/login');
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

  it('createInbound includes unit_cost in the request body when provided', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 1,
          ingredient_id: 1,
          quantity: 10,
          unit_cost: 12.5,
          supplier_name: 'Carnes del Valle S.A.',
          location_id: 1,
          created_at: '2026-07-15T00:00:00Z',
          user_uuid: '1',
        }),
        { status: 200 },
      ),
    );

    const { createInbound } = await import('./inventory');
    await createInbound({
      ingredient_id: 1,
      quantity: 10,
      unit_cost: 12.5,
      supplier_name: 'Carnes del Valle S.A.',
      location_id: 1,
    });

    const [, init] = fetchMock.mock.calls[0]!;
    expect(JSON.parse(String(init?.body))).toEqual({
      ingredient_id: 1,
      quantity: 10,
      unit_cost: 12.5,
      supplier_name: 'Carnes del Valle S.A.',
      location_id: 1,
    });
  });

  it('createInbound omits unit_cost from the request body when not provided', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 1,
          ingredient_id: 1,
          quantity: 10,
          unit_cost: null,
          supplier_name: 'Carnes del Valle S.A.',
          location_id: 1,
          created_at: '2026-07-15T00:00:00Z',
          user_uuid: '1',
        }),
        { status: 200 },
      ),
    );

    const { createInbound } = await import('./inventory');
    await createInbound({
      ingredient_id: 1,
      quantity: 10,
      supplier_name: 'Carnes del Valle S.A.',
      location_id: 1,
    });

    const [, init] = fetchMock.mock.calls[0]!;
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    expect(body).toEqual({
      ingredient_id: 1,
      quantity: 10,
      supplier_name: 'Carnes del Valle S.A.',
      location_id: 1,
    });
    expect('unit_cost' in body).toBe(false);
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
